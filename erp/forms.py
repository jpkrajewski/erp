from django import forms

from erp.models import Invoice, SalesOrder, SalesOrderItem

SalesOrderFormSet = forms.inlineformset_factory(
    SalesOrder, SalesOrderItem, extra=2, exclude=[]
)


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        exclude = ["invoice_number", "status"]
