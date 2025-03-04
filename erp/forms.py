from django import forms
from erp.models import SalesOrder, SalesOrderItem
    
    
SalesOrderFormSet = forms.inlineformset_factory(
    SalesOrder, SalesOrderItem, extra=2, exclude=[]
)