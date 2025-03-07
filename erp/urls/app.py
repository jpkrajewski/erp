from django.urls import path

from erp.views import SalesOrderCreateView, invoice_create_view, invoice_list_view

urlpatterns = [
    path("salesorders/create-form/", SalesOrderCreateView.as_view(), name="salesorder-create-form"),
    path("invoices/create-form/", invoice_create_view, name="invoice-create-form"),
    path("invoices/list/", invoice_list_view, name="invoice-list"),
]
