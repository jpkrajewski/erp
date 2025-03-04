from django.urls import path, include
from rest_framework import routers
from erp.views import SalesOrderModelViewSet, PurchaseOrderModelViewSet, SalesOrderCreateView

erp_router = routers.DefaultRouter()
erp_router.register(r"salesorders", SalesOrderModelViewSet)
erp_router.register(r"purchaseorders", PurchaseOrderModelViewSet)

urlpatterns = [
    path('', include(erp_router.urls)),
    path("salesorders/create/form/", SalesOrderCreateView.as_view(), name="saleorder-create-form")
]
