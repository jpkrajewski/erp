from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Count, Prefetch, Q, Sum
from django.shortcuts import redirect, render, reverse
from django.views.generic.edit import CreateView
from rest_framework import filters, generics, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from erp.forms import InvoiceForm, SalesOrderFormSet
from erp.models import (
    Employee,
    Invoice,
    ManufacturingOrder,
    Product,
    ProductInventory,
    PurchaseOrder,
    QualityCheck,
    SalesOrder,
    Shift,
    Supplier,
    SupplierProduct,
    Warehouse,
    Workstation,
)
from erp.permissions import ExtendedDjangoModelPermission
from erp.serializers import (
    InventoryMoveSerializer,
    ManufacturingOrderSerializer,
    ProductSerializer,
    PurchaseOrderSerializer,
    QualityCheckSerializer,
    SalesOrderSerializer,
    SupplierSerializer,
    WarehouseInventorySerializer,
    WarehouseSerializer,
    WorkshiftListSerializer,
    WorkstationSerializer,
)


class SmallSizePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 1000



# ---------------------------------------------------
# Product & Inventory Management System
# ---------------------------------------------------
class InventoryMoveView(APIView):
    """
    API endpoint to move inventory (transfer quantity of a product) from one warehouse to another.
    """

    def post(self, request, *args, **kwargs):
        serializer = InventoryMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from_warehouse_id = data["from_warehouse"]
        to_warehouse_id = data["to_warehouse"]
        product_id = data["product"]
        quantity = data["quantity"]

        try:
            Warehouse.objects.get(id=from_warehouse_id)
            Warehouse.objects.get(id=to_warehouse_id)
        except Warehouse.DoesNotExist:
            return Response({"error": "Warehouse does not exist"}, status=404)

        try:
            Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product does not exist"}, status=404)

        with transaction.atomic():
            try:
                source_inventory = ProductInventory.objects.select_for_update().get(
                    warehouse_id=from_warehouse_id, product_id=product_id
                )
            except ProductInventory.DoesNotExist:
                return Response(
                    {"error": "Product does not exist in the from warehouse"},
                    status=404,
                )

            if source_inventory.quantity < quantity:
                return Response(
                    {"error": "Not enough quantity in the from warehouse"}, status=400
                )

            source_inventory.quantity -= quantity
            source_inventory.save()

            destination_inventory, created = ProductInventory.objects.get_or_create(
                warehouse_id=to_warehouse_id,
                product_id=product_id,
                defaults={"quantity": 0},
            )
            destination_inventory.quantity += quantity
            destination_inventory.save()

        return Response(
            {
                "success": "Inventory moved successfully",
                "inventoryId": destination_inventory.id,
            },
            status=200,
        )


class ProductModelViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = (
        Product.objects.all()
        .prefetch_related(
            Prefetch(
                "suppliers",
                queryset=SupplierProduct.objects.filter(is_preferred=True),
                to_attr="preferred_suppliers",
            )
        )
        .annotate(total_quantity=Sum("inventory__quantity"))
    )
    pagination_class = SmallSizePagination


class SupplierModelViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    queryset = Supplier.objects.all().prefetch_related("products")
    pagination_class = SmallSizePagination


class WarehouseModelViewSet(viewsets.ModelViewSet):
    serializer_class = WarehouseSerializer
    queryset = Warehouse.objects.all()
    pagination_class = SmallSizePagination


class WarehouseInventoryView(generics.RetrieveAPIView):
    queryset = Warehouse.objects.all().prefetch_related("inventory")
    serializer_class = WarehouseInventorySerializer


# ---------------------------------------------------
# Manufacturing Module
# ---------------------------------------------------


class WorkstationModelViewSet(viewsets.ModelViewSet):
    serializer_class = WorkstationSerializer

    def get_queryset(self):
        """
        Return different querysets based on the action.
        """
        # Check if the current action is 'list'
        if self.action == 'list':
            # Customize the queryset for the list action (for example, get all Workstations)
            return Workstation.objects.all().prefetch_related(
                Prefetch("shifts", queryset=Shift.objects.filter(
                    Q(status="IN_PROGRESS") | Q(status="ABSENT")
                )
                )
            ).annotate(
                    total_shifts=Count("shifts"),
                    total_shifts_in_progress=Count(
                        "shifts", filter=Q(shifts__status="IN_PROGRESS")
                    ),
                    total_shifts_absent=Count(
                        "shifts", filter=Q(shifts__status="ABSENT")
                    ),
            )
        else:
            # Default queryset for other actions (create, retrieve, etc.)
            return Workstation.objects.all().prefetch_related(
                Prefetch("shifts", queryset=Shift.objects.filter(
                    Q(status="IN_PROGRESS") | Q(status="ABSENT")
                ).select_related("employee").order_by("status", "end_time"))
            )

    def get_serializer_class(self):
        """
        Return different serializer classes based on the action.
        """
        # Check if the current action is 'list'
        if self.action == 'list':
            # Customize the serializer for the list action
            return WorkshiftListSerializer
        else:
            # Default serializer for other actions
            return WorkstationSerializer

# ---------------------------------------------------
#  Sales & Order Management Module
# ---------------------------------------------------


class SalesOrderModelViewSet(viewsets.ModelViewSet):
    serializer_class = SalesOrderSerializer
    queryset = SalesOrder.objects.all()


class PurchaseOrderModelViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer
    queryset = PurchaseOrder.objects.all()


class QualityCheckSerializerModelViewSet(viewsets.ModelViewSet):
    serializer_class = QualityCheckSerializer
    queryset = QualityCheck.objects.all()
    permission_classes = [ExtendedDjangoModelPermission]


class ManufacturingOrderModelViewSet(viewsets.ModelViewSet):
    serializer_class = ManufacturingOrderSerializer
    queryset = ManufacturingOrder.objects.all()
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]


class SalesOrderCreateView(CreateView):
    model = SalesOrder
    form_class = forms.modelform_factory(SalesOrder, exclude=["total_amount", "actual_delivery", "order_number", "order_date", "created_by"])
    template_name = "salesorder_form.html"

    def get_context_data(self, **kwargs):
        """Add formset to the context"""
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["formset"] = SalesOrderFormSet(self.request.POST)
        else:
            context["formset"] = SalesOrderFormSet()
        return context

    def form_valid(self, form):
        """Handle formset saving"""
        context = self.get_context_data()
        formset = context["formset"]

        total = 0
        if formset.is_valid():
            total = 0
            for item_form in formset.forms:
                # Example calculation for total amount, assuming quantity, unit_price, and discount_percentage exist
                total += (
                    (
                        item_form.cleaned_data["quantity"]
                        * item_form.cleaned_data["unit_price"]
                    )
                    * (100 - item_form.cleaned_data["discount_percentage"])
                    / 100
                )

            form.total_amount = total
            form.created_by = self.request.user
            self.object = form.save()  # Save the SalesOrder first
            formset.instance = (
                self.object
            )  # Link SalesOrderItem to the saved SalesOrder
            formset.save()  # Save the formset

            return redirect(
                reverse("salesorder-list")
            )  # Redirect to list view after save
        else:
            return self.render_to_response(self.get_context_data(form=form))



@login_required(login_url="/accounts/login/")
def user_profile_view(request):
    try:
        # Try to get the existing employee profile
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        # If employee profile does not exist, create it
        employee = Employee.create_initial_employee_profile(request.user)

    # Pass the employee object to the template to display the profile
    return render(request, "user_profile.html", {"employee": employee})

@permission_required("erp.add_invoice")
def invoice_create_view(request):
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.invoice_number = Invoice.generate_invoice_number()
            invoice.status = "PENDING"
            invoice.save()
            return redirect("invoice-list")
    else:
        form = InvoiceForm()
    return render(request, "invoice_form.html", {"form": form})

# @permission_required("erp.view_invoice")
def invoice_list_view(request):
    invoices = Invoice.objects.all().order_by("-created_at")
    return render(request, "invoice_list.html", {"invoices": invoices})
