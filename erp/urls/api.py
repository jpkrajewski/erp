from django.urls import include, path
from rest_framework import routers

from erp.views import (
    InventoryMoveView,
    ManufacturingOrderModelViewSet,
    ProductModelViewSet,
    PurchaseOrderModelViewSet,
    SalesOrderModelViewSet,
    SupplierModelViewSet,
    WarehouseInventoryView,
    WarehouseModelViewSet,
    WorkstationModelViewSet,
)

erp_router = routers.DefaultRouter()
# ---------------------------------------------------
# Product & Inventory Management System
# ---------------------------------------------------
erp_router.register(r"products", ProductModelViewSet)
erp_router.register(r"suppliers", SupplierModelViewSet)
erp_router.register(r"warehouses", WarehouseModelViewSet)

# ---------------------------------------------------
# Manufacturing Module
# ---------------------------------------------------
erp_router.register(r"manufacturing-orders", ManufacturingOrderModelViewSet)
erp_router.register(r"workstations", WorkstationModelViewSet, basename='workstation')

# ---------------------------------------------------
# Sales & Purchase Module
# ---------------------------------------------------
erp_router.register(r"salesorders", SalesOrderModelViewSet)
erp_router.register(r"purchaseorders", PurchaseOrderModelViewSet)



urlpatterns = [
    path("", include(erp_router.urls)),
    path("inventory/move/", InventoryMoveView.as_view(), name="inventory-move"),
    path(
        "warehouses/<int:pk>/inventory/",
        WarehouseInventoryView.as_view(),
        name="warehouse-inventory",
    ),
]
