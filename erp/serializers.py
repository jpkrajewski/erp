from django.db import models
from rest_framework import serializers

from erp.models import (
    ManufacturingOrder,
    ManufacturingStep,
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


# ---------------------------------------------------
# Implement the Product & Inventory Management System
# ---------------------------------------------------
class InventoryMoveSerializer(serializers.Serializer):
    from_warehouse = serializers.IntegerField()
    to_warehouse = serializers.IntegerField()
    product = serializers.IntegerField()
    quantity = serializers.IntegerField()

    def validate(self, data):
        if data["from_warehouse"] == data["to_warehouse"]:
            raise serializers.ValidationError(
                "Cannot move product to the same warehouse"
            )
        return data


class SupplierProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierProduct
        exclude = ["supplier"]


class SupplierSerializer(serializers.ModelSerializer):
    products = SupplierProductSerializer(many=True)

    class Meta:
        model = Supplier
        fields = "__all__"


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = "__all__"


class WarehouseInventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInventory
        fields = "__all__"


class WorkstationShiftSerializer(serializers.ModelSerializer):
    employee_id = serializers.CharField(source="employee.employee_id", read_only=True)
    employee_first_name = serializers.CharField(source="employee.first_name", read_only=True)
    employee_last_name = serializers.CharField(source="employee.last_name", read_only=True)
    class Meta:
        model = Shift
        fields = ["manufacturing_order", "employee_id", "employee_first_name", "employee_last_name", "start_time", "end_time", "status"]

class WorkstationSerializer(serializers.ModelSerializer):
    shifts = WorkstationShiftSerializer(many=True, read_only=True)
    class Meta:
        model = Workstation
        fields = "__all__"


class WorkshiftListSerializer(serializers.ModelSerializer):
    total_shifts = serializers.IntegerField(read_only=True)
    total_shifts_in_progress = serializers.IntegerField(read_only=True)
    total_shifts_absent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Workstation
        fields = "__all__"


class SalesOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = "__all__"


class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = "__all__"



class QualityCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityCheck
        fields = "__all__"


class PreferredProductSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierProduct
        fields = ["supplier", "unit_cost"]


class ProductSerializer(serializers.ModelSerializer):
    preferred_suppliers = PreferredProductSupplierSerializer(many=True)
    total_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = "__all__"


class WarehouseProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name"]


class ProductInventorySerializer(serializers.ModelSerializer):
    product = WarehouseProductSerializer()

    class Meta:
        model = ProductInventory
        fields = ["id", "quantity", "product"]


class WarehouseInventorySerializer(serializers.ModelSerializer):
    inventory = ProductInventorySerializer(read_only=True, many=True)
    total_product_quantity = serializers.SerializerMethodField()

    class Meta:
        model = Warehouse
        fields = [
            "id",
            "name",
            "inventory",
            "location",
            "capacity",
            "manager",
            "total_product_quantity",
        ]

    def get_total_product_quantity(self, obj):
        obj.inventory.aggregate(models.Sum("quantity"))["quantity__sum"]


class ManufacturingStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManufacturingStep
        fields = ["id", "name", "description", "status"]


class ManufacturingOrderSerializer(serializers.ModelSerializer):
    steps = ManufacturingStepSerializer(many=True, read_only=True)

    class Meta:
        model = ManufacturingOrder
        fields = [
            "id",
            "product",
            "quantity",
            "status",
            "steps",
            "bom_version",
            "priority",
            "start_date",
            "estimated_completion",
            "order_number",
        ]
