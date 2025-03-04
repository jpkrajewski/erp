from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import User

# -------------------------
# 1️⃣ Inventory & Warehousing
# -------------------------
class Warehouse(models.Model):
    name = models.CharField(max_length=255)  # Warehouse Name
    location = models.CharField(max_length=255)  # Address or Factory Section
    capacity = models.PositiveIntegerField()  # Max storage capacity
    manager = models.CharField(max_length=255, null=True, blank=True)  # Warehouse manager
    contact_email = models.EmailField(null=True, blank=True)  # Contact information
    contact_phone = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)  # For future warehouse deactivation
    notes = models.TextField(null=True, blank=True)  # Additional information
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    PRODUCT_CATEGORIES = [
        ('RAW', 'Raw Material'),
        ('WIP', 'Work In Progress'),
        ('FIN', 'Finished Product'),
        ('TOOL', 'Tool/Equipment'),
        ('SPARE', 'Spare Part'),
    ]
    
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=10, choices=PRODUCT_CATEGORIES, default='FIN')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_stock_level = models.PositiveIntegerField(default=0)  # For reorder alerts
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField(max_length=100, null=True, blank=True)  # e.g., "10x20x30 cm"
    warehouses = models.ManyToManyField(Warehouse, through='ProductInventory', related_name='products')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def get_total_quantity(self):
        """Get total quantity across all warehouses"""
        return sum(inv.quantity for inv in self.inventory.all())

class ProductInventory(models.Model):
    """Junction table for the many-to-many relationship between Product and Warehouse"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.PositiveIntegerField(default=0)
    location_code = models.CharField(max_length=50, null=True, blank=True)  # Aisle-Rack-Shelf code
    last_counted = models.DateField(null=True, blank=True)  # For inventory audits
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'warehouse']
        verbose_name_plural = "Product Inventories"

    def __str__(self):
        return f"{self.product.name} at {self.warehouse.name}: {self.quantity} units"

# -------------------------
# 2️⃣ Suppliers & Purchase Orders
# -------------------------
class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    website = models.URLField(null=True, blank=True)
    payment_terms = models.CharField(max_length=100, null=True, blank=True)  # e.g., "Net 30"
    supplier_rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5 rating
    is_active = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def get_supplied_products(self):
        """Get all products this supplier provides"""
        return Product.objects.filter(supplierproduct__supplier=self)

class SupplierProduct(models.Model):
    """Products that a supplier can provide"""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='suppliers')
    supplier_sku = models.CharField(max_length=50, null=True, blank=True)  # Supplier's product code
    lead_time_days = models.PositiveIntegerField(default=0)  # Typical delivery time
    min_order_quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_preferred = models.BooleanField(default=False)  # Preferred supplier for this product
    
    class Meta:
        unique_together = ['supplier', 'product']
    
    def __str__(self):
        return f"{self.product.name} from {self.supplier.name}"

class PurchaseOrderManager(models.Manager):
    def recent(self):
        return self.filter(order_date__gte=timezone.datetime.today() - timezone.timedelta(days=30))

    def pending(self):
        return self.filter(status="PENDING")

class PurchaseOrder(models.Model):
    objects = PurchaseOrderManager()
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('ORDERED', 'Ordered'),
        ('PARTIAL', 'Partially Received'),
        ('RECEIVED', 'Received'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="purchase_orders")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="purchase_orders")
    order_date = models.DateField(default=timezone.now)
    expected_delivery = models.DateField()
    actual_delivery = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=[
        ('UNPAID', 'Unpaid'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Paid')
    ], default='UNPAID')
    notes = models.TextField(null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)  # User who created PO
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    expected_delivery = models.DateField(null=True, blank=True)  # Item-specific delivery date
    
    def __str__(self):
        return f"{self.quantity_ordered} x {self.product.name} on {self.purchase_order.po_number}"
    
    def line_total(self):
        return self.quantity_ordered * self.unit_price

# -------------------------
# 3️⃣ Customers & Sales
# -------------------------
class Customer(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    shipping_address = models.TextField(null=True, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    customer_since = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class SalesOrderQuerySet(models.QuerySet):
    def expensive_order(self):
        return self.filter(total_amount__gte=10000)
    
    def with_notes(self):
        return self.filter(notes__isnull=False)
    

class SalesOrderQueryManager(models.Manager):
    def get_queryset(self):
        return SalesOrderQuerySet(self.model, using=self._db)


class SalesOrder(models.Model):
    objects = SalesOrderQueryManager()
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('READY', 'Ready for Shipment'),
        ('PARTIAL', 'Partially Shipped'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="sales_orders")
    order_date = models.DateField(default=timezone.now)
    requested_delivery = models.DateField()
    actual_delivery = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    shipping_method = models.CharField(max_length=100, null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order_number} - {self.customer.name} ({self.status})"
    
    def get_manufacturing_orders(self):
        """Get all manufacturing orders associated with this sales order"""
        return ManufacturingOrder.objects.filter(sales_order_item__sales_order=self)

class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} on {self.sales_order.order_number}"
    
    def line_total(self):
        return self.quantity * self.unit_price * (1 - self.discount_percentage / 100)

class Invoice(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="invoices")
    invoice_number = models.CharField(max_length=50, unique=True)
    issued_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('ISSUED', 'Issued'),
        ('PARTIAL', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ], default='ISSUED')
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.invoice_number} for {self.sales_order.order_number}"

# -------------------------
# 4️⃣ Manufacturing & Production
# -------------------------
class Workstation(models.Model):
    name = models.CharField(max_length=100)
    machine_id = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    maintenance_schedule = models.CharField(max_length=255, null=True, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('OPERATIONAL', 'Operational'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('BREAKDOWN', 'Breakdown'),
        ('INACTIVE', 'Inactive'),
    ], default='OPERATIONAL')
    capacity_per_hour = models.PositiveIntegerField(null=True, blank=True)  # Production capacity
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.machine_id})"

class ProcessTemplate(models.Model):
    """Template for manufacturing processes that can be reused"""
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    estimated_time = models.PositiveIntegerField(help_text="Estimated time in minutes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class ProcessStep(models.Model):
    """Individual steps in a process template"""
    process = models.ForeignKey(ProcessTemplate, on_delete=models.CASCADE, related_name='steps')
    sequence = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField()
    workstation_type = models.CharField(max_length=100, null=True, blank=True)
    estimated_time = models.PositiveIntegerField(help_text="Estimated time in minutes")
    
    class Meta:
        ordering = ['sequence']
    
    def __str__(self):
        return f"{self.process.name} - Step {self.sequence}: {self.name}"

class BillOfMaterials(models.Model):
    """Bill of Materials for products"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='bom')
    process_template = models.ForeignKey(ProcessTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Bills of Materials"
    
    def __str__(self):
        return f"BOM for {self.product.name} v{self.version}"

class BOMItem(models.Model):
    """Components required in a Bill of Materials"""
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='items')
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='used_in')
    quantity_required = models.DecimalField(max_digits=10, decimal_places=3)
    unit_of_measure = models.CharField(max_length=20, default='units')
    step = models.ForeignKey(ProcessStep, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.quantity_required} {self.unit_of_measure} of {self.component.name} for {self.bom.product.name}"

class ManufacturingOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PLANNED', 'Planned'),
        ('MATERIAL_PENDING', 'Materials Pending'),
        ('READY', 'Ready to Start'),
        ('IN_PROGRESS', 'In Progress'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="manufacturing_orders")
    bom_version = models.CharField(max_length=20, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    sales_order_item = models.ForeignKey(
        SalesOrderItem, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name="manufacturing_orders"
    )
    target_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, related_name="production_orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    priority = models.PositiveSmallIntegerField(default=5)  # 1-10 priority scale
    start_date = models.DateField()
    estimated_completion = models.DateField()
    actual_completion = models.DateField(null=True, blank=True)
    production_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"MO-{self.order_number} - {self.product.name} ({self.status})"
    
    def units_completed(self):
        """Calculate total units completed so far"""
        return sum(log.units_produced for log in self.logs.all())
    
    def get_sales_order(self):
        """Get related sales order if exists"""
        if self.sales_order_item:
            return self.sales_order_item.sales_order
        return None

class ManufacturingStep(models.Model):
    """Individual manufacturing steps for a specific manufacturing order"""
    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='steps')
    process_step = models.ForeignKey(ProcessStep, on_delete=models.SET_NULL, null=True, blank=True)
    sequence = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    workstation = models.ForeignKey(Workstation, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('SKIPPED', 'Skipped'),
    ], default='PENDING')
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['sequence']
    
    def __str__(self):
        return f"{self.manufacturing_order.order_number} - Step {self.sequence}: {self.name}"

class ProductionLog(models.Model):
    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name="logs")
    manufacturing_step = models.ForeignKey(ManufacturingStep, on_delete=models.SET_NULL, null=True, blank=True)
    workstation = models.ForeignKey(Workstation, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    units_produced = models.PositiveIntegerField(default=0)
    units_defective = models.PositiveIntegerField(default=0)
    downtime_minutes = models.PositiveIntegerField(default=0)
    downtime_reason = models.CharField(max_length=255, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Log for {self.manufacturing_order} on {self.date}"

class QualityCheck(models.Model):
    """Quality control checks for production"""
    production_log = models.ForeignKey(ProductionLog, on_delete=models.CASCADE, related_name='quality_checks')
    check_type = models.CharField(max_length=50)  # e.g., "Visual", "Dimensional", "Functional"
    result = models.CharField(max_length=20, choices=[
        ('PASS', 'Pass'),
        ('FAIL', 'Fail'),
        ('WARNING', 'Warning')
    ])
    measurement = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    checked_by = models.CharField(max_length=100)
    checked_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.check_type} check for {self.production_log}"

# -------------------------
# 5️⃣ Employee & Shift Management
# -------------------------
class Employee(models.Model):
    employee_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    department = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    workstation = models.ForeignKey(Workstation, on_delete=models.SET_NULL, null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Shift(models.Model):
    SHIFT_TYPES = [
        ('MORNING', 'Morning (6AM-2PM)'),
        ('AFTERNOON', 'Afternoon (2PM-10PM)'),
        ('NIGHT', 'Night (10PM-6AM)'),
        ('CUSTOM', 'Custom Hours')
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='shifts')
    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='shifts')
    manufacturing_step = models.ForeignKey(ManufacturingStep, on_delete=models.SET_NULL, null=True, blank=True)
    workstation = models.ForeignKey(Workstation, on_delete=models.SET_NULL, null=True, blank=True)
    shift_date = models.DateField()
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPES, default='MORNING')
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_minutes = models.PositiveIntegerField(default=30)
    overtime_minutes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ABSENT', 'Absent'),
        ('CANCELLED', 'Cancelled')
    ], default='SCHEDULED')
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} on {self.shift_date} ({self.shift_type})"
    
    def shift_hours(self):
        """Calculate total shift hours excluding breaks"""
        start = timezone.datetime.combine(timezone.datetime.today(), self.start_time)
        end = timezone.datetime.combine(timezone.datetime.today(), self.end_time)
        if end < start:  # Handle overnight shifts
            end += timezone.timedelta(days=1)
        total_minutes = (end - start).total_seconds() / 60 - self.break_minutes
        return total_minutes / 60

# -------------------------
# 6️⃣ Maintenance & Equipment
# -------------------------
class MaintenanceSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('SEMI_ANNUAL', 'Semi-Annual'),
        ('ANNUAL', 'Annual'),
        ('USAGE_BASED', 'Based on Usage'),
    ]
    
    workstation = models.ForeignKey(Workstation, on_delete=models.CASCADE, related_name='maintenance_schedules')
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    usage_threshold = models.PositiveIntegerField(null=True, blank=True)  # For usage-based maintenance
    estimated_downtime = models.PositiveIntegerField(help_text="Estimated downtime in minutes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} for {self.workstation.name} ({self.frequency})"

class MaintenanceActivity(models.Model):
    workstation = models.ForeignKey(Workstation, on_delete=models.CASCADE, related_name='maintenance_activities')
    schedule = models.ForeignKey(MaintenanceSchedule, on_delete=models.SET_NULL, null=True, blank=True)
    maintenance_type = models.CharField(max_length=50, choices=[
        ('PREVENTIVE', 'Preventive'),
        ('CORRECTIVE', 'Corrective'),
        ('PREDICTIVE', 'Predictive'),
        ('EMERGENCY', 'Emergency'),
    ])
    description = models.TextField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ], default='SCHEDULED')
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    performed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.maintenance_type} maintenance for {self.workstation.name} on {self.start_datetime.date()}"
    
    def downtime_hours(self):
        if not self.end_datetime:
            return None
        delta = self.end_datetime - self.start_datetime
        return delta.total_seconds() / 3600

# -------------------------
# 7️⃣ Reporting & Analytics
# -------------------------
class ProductionKPI(models.Model):
    """Key Performance Indicators for production"""
    date = models.DateField()
    workstation = models.ForeignKey(Workstation, on_delete=models.CASCADE, related_name='kpis', null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='kpis', null=True, blank=True)
    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE)
    
# -------------------------
# 8️⃣ Currency & Exchange Rates
# -------------------------
class CurrencyRate(models.Model):
    currency_code = models.CharField(max_length=3, unique=True)  # ISO 4217 currency code
    exchange_rate = models.DecimalField(max_digits=20, decimal_places=10)  # Using high precision for rates
    last_updated = models.DateTimeField(auto_now=True)  # Automatically updated whenever the record is saved

    def __str__(self):
        return f"{self.currency_code}: {self.exchange_rate} with USD"