from django.shortcuts import render, redirect, reverse
from rest_framework import viewsets
from django.views.generic.edit import CreateView
from erp.models import SalesOrder, PurchaseOrder, Invoice, Workstation
from erp.serializers import SalesOrderSerializer, PurchaseOrderSerializer, WorkstationSerializer
from erp.forms import SalesOrderFormSet
from django import forms

# Create your views here.
class SalesOrderModelViewSet(viewsets.ModelViewSet):
    serializer_class = SalesOrderSerializer
    queryset = SalesOrder.objects.all()
    
    
class PurchaseOrderModelViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer
    queryset = PurchaseOrder.objects.all()
    

class WorkstationSerializerModelViewSet(viewsets.ModelViewSet):
    serializer_class = WorkstationSerializer
    queryset = Workstation.objects.all()
    


class SalesOrderCreateView(CreateView):
    model = SalesOrder
    form_class = forms.modelform_factory(SalesOrder, exclude=["total_amount"])
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
                total += (item_form.cleaned_data['quantity'] * item_form.cleaned_data['unit_price']) * (100 - item_form.cleaned_data['discount_percentage']) / 100

            form.total_amount = total
            self.object = form.save()  # Save the SalesOrder first
            formset.instance = self.object  # Link SalesOrderItem to the saved SalesOrder
            formset.save()  # Save the formset

            return redirect(reverse("salesorder-list"))  # Redirect to list view after save
        else:
            return self.render_to_response(self.get_context_data(form=form))

# class InvoiceCreateView():