from rest_framework import serializers
from erp.models import SalesOrder, PurchaseOrder, Workstation

class SalesOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrder
        fields = "__all__"
        
        
class PurchaseOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrder
        fields = "__all__"
        

class WorkstationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workstation
        fields = "__all__"