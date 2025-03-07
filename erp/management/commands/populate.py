import datetime
import decimal
import os
import random

import django
import numpy as np
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker
from tqdm import tqdm

# Import models after Django setup
from erp.models import (
    BillOfMaterials,
    BOMItem,
    Customer,
    Employee,
    Invoice,
    MaintenanceActivity,
    MaintenanceSchedule,
    ManufacturingOrder,
    ManufacturingStep,
    OrderNumber,
    ProcessStep,
    ProcessTemplate,
    Product,
    ProductInventory,
    ProductionKPI,
    ProductionLog,
    PurchaseOrder,
    PurchaseOrderItem,
    QualityCheck,
    SalesOrder,
    SalesOrderItem,
    Shift,
    Supplier,
    SupplierProduct,
    Warehouse,
    Workstation,
)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()


# Initialize Faker
fake = Faker()

# Configuration
NUM_WAREHOUSES = 10
NUM_PRODUCTS = 500
NUM_SUPPLIERS = 50
NUM_CUSTOMERS = 200
NUM_WORKSTATIONS = 30
NUM_EMPLOYEES = 100
NUM_PROCESS_TEMPLATES = 30
NUM_PURCHASE_ORDERS = 500
NUM_SALES_ORDERS = 1000
NUM_MANUFACTURING_ORDERS = 2000
YEARS_OF_DATA = 5  # How many years of historical data to generate

# Helper functions
def random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    if start_date >= end_date:
        return start_date  # or handle this case as needed
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + datetime.timedelta(days=random_days)

def random_decimal(min_value, max_value, decimal_places=2):
    """Generate a random decimal between min_value and max_value"""
    min_value = float(min_value)
    max_value = float(max_value)

    return decimal.Decimal(random.uniform(min_value, max_value)).quantize(
        decimal.Decimal('0.' + '0' * decimal_places)
    )

def weighted_choice(choices, weights):
    """Make a weighted random choice from a list"""
    cumulative_weights = np.cumsum(weights)
    total = cumulative_weights[-1]
    rand = random.uniform(0, total)
    for i, weight in enumerate(cumulative_weights):
        if rand <= weight:
            return choices[i]

def generate_sku():
    """Generate a unique SKU"""
    prefix = random.choice(['P', 'R', 'T', 'S', 'E'])
    category = random.choice(['A', 'B', 'C', 'D', 'E'])
    number = random.randint(10000, 99999)
    return f"{prefix}{category}-{number}"

def generate_order_number(prefix, id_value):
    """Generate an order number with a specific prefix and ID padding"""
    return f"{prefix}-{id_value:06d}"

def get_future_date(base_date, min_days=1, max_days=60):
    """Generate a future date from base_date"""
    return base_date + datetime.timedelta(days=random.randint(min_days, max_days))

def createsuperuser():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@admin.com', 'admin')

@transaction.atomic
def create_order_number():
    OrderNumber().save()

@transaction.atomic
def create_warehouses():
    """Create warehouse records"""
    print("Creating warehouses...")
    warehouses = []
    for i in range(1, NUM_WAREHOUSES + 1):
        capacity = random.randint(10000, 100000)
        warehouse = Warehouse(
            name=f"Warehouse {fake.city()}",
            location=fake.address(),
            capacity=capacity,
            manager=fake.name(),
            contact_email=fake.company_email(),
            contact_phone=fake.phone_number(),
            is_active=True,
            notes=fake.text(max_nb_chars=200) if random.random() > 0.7 else None
        )
        warehouses.append(warehouse)

    Warehouse.objects.bulk_create(warehouses)
    print(f"Created {len(warehouses)} warehouses")
    return Warehouse.objects.all()

@transaction.atomic
def create_products(warehouses):
    """Create product records"""
    print("Creating products...")
    products = []
    categories = ['RAW', 'WIP', 'FIN', 'TOOL', 'SPARE']
    category_weights = [0.3, 0.2, 0.3, 0.1, 0.1]

    for i in tqdm(range(1, NUM_PRODUCTS + 1)):
        category = weighted_choice(categories, category_weights)
        unit_price = random_decimal(10, 5000) if category in ['FIN', 'TOOL'] else random_decimal(1, 1000)
        unit_cost = random_decimal(unit_price *  decimal.Decimal(0.4), unit_price *  decimal.Decimal(0.8))
        min_stock = random.randint(5, 100)

        product = Product(
            name=f"{fake.word().capitalize()} {fake.word().capitalize()}" + (" Tool" if category == 'TOOL' else ""),
            sku=generate_sku(),
            description=fake.text(max_nb_chars=200) if random.random() > 0.3 else None,
            category=category,
            unit_price=unit_price,
            unit_cost=unit_cost,
            min_stock_level=min_stock,
            weight=random_decimal(0.1, 100) if random.random() > 0.3 else None,
            dimensions=f"{random.randint(1, 100)}x{random.randint(1, 100)}x{random.randint(1, 100)} cm" if random.random() > 0.3 else None,
            is_active=True
        )
        products.append(product)

    Product.objects.bulk_create(products)
    print(f"Created {len(products)} products")

    # Create product inventory (distribute products across warehouses)
    print("Creating product inventory...")
    inventory_records = []
    products = Product.objects.all()

    for product in tqdm(products):
        # Each product exists in 1-4 warehouses
        num_warehouses = random.randint(1, min(4, len(warehouses)))
        product_warehouses = random.sample(list(warehouses), num_warehouses)

        for warehouse in product_warehouses:
            # Calculate quantity based on product category
            if product.category == 'FIN':
                quantity = random.randint(10, 200)
            elif product.category == 'RAW':
                quantity = random.randint(50, 1000)
            elif product.category == 'WIP':
                quantity = random.randint(5, 50)
            elif product.category == 'TOOL':
                quantity = random.randint(1, 20)
            else:  # SPARE
                quantity = random.randint(10, 100)

            inventory = ProductInventory(
                product=product,
                warehouse=warehouse,
                quantity=quantity,
                location_code=f"{random.choice('ABCDEFGH')}-{random.randint(1, 99)}-{random.randint(1, 999)}",
                last_counted=random_date(timezone.now() - datetime.timedelta(days=90), timezone.now()) if random.random() > 0.5 else None
            )
            inventory_records.append(inventory)

    ProductInventory.objects.bulk_create(inventory_records)
    print(f"Created {len(inventory_records)} inventory records")
    return Product.objects.all()

@transaction.atomic
def create_suppliers():
    """Create supplier records"""
    print("Creating suppliers...")
    suppliers = []

    for i in range(1, NUM_SUPPLIERS + 1):
        payment_terms = random.choice(['Net 30', 'Net 45', 'Net 60', '2/10 Net 30', 'COD'])
        supplier = Supplier(
            name=fake.company(),
            contact_person=fake.name(),
            email=fake.company_email(),
            phone=fake.phone_number(),
            address=fake.address(),
            website=fake.url() if random.random() > 0.3 else None,
            payment_terms=payment_terms,
            supplier_rating=random.randint(1, 5) if random.random() > 0.2 else None,
            is_active=True,
            notes=fake.text(max_nb_chars=200) if random.random() > 0.7 else None
        )
        suppliers.append(supplier)

    Supplier.objects.bulk_create(suppliers)
    print(f"Created {len(suppliers)} suppliers")
    return Supplier.objects.all()

@transaction.atomic
def create_supplier_products(suppliers, products):
    """Create supplier product relationships"""
    print("Creating supplier product relationships...")
    supplier_products = []
    raw_materials = Product.objects.filter(category='RAW')
    parts = Product.objects.filter(category__in=['SPARE', 'TOOL'])

    # Each supplier supplies a random subset of raw materials and parts
    for supplier in tqdm(suppliers):
        # Determine how many products this supplier provides
        num_raw = random.randint(5, min(20, raw_materials.count()))
        num_parts = random.randint(3, min(15, parts.count()))

        supplier_raw_materials = random.sample(list(raw_materials), num_raw)
        supplier_parts = random.sample(list(parts), num_parts)

        for product in supplier_raw_materials + supplier_parts:
            lead_time = random.randint(1, 45)  # 1 to 45 days lead time
            min_order = random.randint(1, 100)
            unit_cost = random_decimal(product.unit_cost * decimal.Decimal(0.8), product.unit_cost * decimal.Decimal(1.2))

            sp = SupplierProduct(
                supplier=supplier,
                product=product,
                supplier_sku=f"S{random.randint(10000, 99999)}" if random.random() > 0.3 else None,
                lead_time_days=lead_time,
                min_order_quantity=min_order,
                unit_cost=unit_cost,
                is_preferred=random.random() > 0.8  # 20% chance to be preferred
            )
            supplier_products.append(sp)

    SupplierProduct.objects.bulk_create(supplier_products)
    print(f"Created {len(supplier_products)} supplier product relationships")

@transaction.atomic
def create_customers():
    """Create customer records"""
    print("Creating customers...")
    customers = []

    for i in range(1, NUM_CUSTOMERS + 1):
        date_created = random_date(timezone.now() - datetime.timedelta(days=365 * YEARS_OF_DATA), timezone.now())
        customer = Customer(
            name=fake.company(),
            contact_person=fake.name() if random.random() > 0.2 else None,
            email=fake.company_email(),
            phone=fake.phone_number(),
            address=fake.address(),
            shipping_address=fake.address() if random.random() > 0.7 else None,
            credit_limit=random_decimal(5000, 500000) if random.random() > 0.3 else None,
            customer_since=date_created.date(),
            is_active=True,
            notes=fake.text(max_nb_chars=200) if random.random() > 0.8 else None
        )
        customers.append(customer)

    Customer.objects.bulk_create(customers)
    print(f"Created {len(customers)} customers")
    return Customer.objects.all()

@transaction.atomic
def create_workstations():
    """Create workstation records"""
    print("Creating workstations...")
    workstations = []

    workstation_types = [
        'Assembly Line', 'CNC Machine', 'Welding Station', 'Painting Booth',
        'Quality Control', 'Packaging', 'Molding', 'Cutting', 'Grinding', 'Testing'
    ]

    for i in range(1, NUM_WORKSTATIONS + 1):
        ws_type = random.choice(workstation_types)
        capacity = random.randint(5, 100)
        last_maintenance = random_date(timezone.now() - datetime.timedelta(days=180), timezone.now())

        workstation = Workstation(
            name=f"{ws_type} {i}",
            machine_id=f"WS-{random.randint(1000, 9999)}",
            location=f"Building {random.choice('ABCD')}, Floor {random.randint(1, 3)}, Section {random.randint(1, 10)}",
            description=fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
            maintenance_schedule=f"Every {random.randint(1, 6)} months" if random.random() > 0.3 else None,
            last_maintenance=last_maintenance,
            status=weighted_choice(
                ['OPERATIONAL', 'MAINTENANCE', 'BREAKDOWN', 'INACTIVE'],
                [0.85, 0.10, 0.03, 0.02]
            ),
            capacity_per_hour=capacity,
            is_active=True
        )
        workstations.append(workstation)

    Workstation.objects.bulk_create(workstations)
    print(f"Created {len(workstations)} workstations")
    return Workstation.objects.all()

@transaction.atomic
def create_employees(workstations):
    """Create employee records"""
    print("Creating employees...")
    employees = []

    roles = [
        'Production Worker', 'Machine Operator', 'Quality Inspector', 'Shift Supervisor',
        'Maintenance Technician', 'Production Planner', 'Warehouse Associate', 'Team Lead'
    ]

    departments = [
        'Production', 'Quality Control', 'Maintenance', 'Logistics', 'Planning'
    ]

    for i in range(1, NUM_EMPLOYEES + 1):
        role = random.choice(roles)
        department = random.choice(departments)

        # Assign workstation based on role
        if role in ['Machine Operator', 'Production Worker']:
            workstation = random.choice(workstations) if random.random() > 0.1 else None
        elif role == 'Maintenance Technician':
            workstation = None  # Maintenance techs not assigned to specific workstations
        elif role == 'Quality Inspector':
            qc_stations = [ws for ws in workstations if 'Quality' in ws.name]
            workstation = random.choice(qc_stations) if qc_stations else None
        else:
            workstation = None

        hire_date = random_date(timezone.now() - datetime.timedelta(days=365 * 5), timezone.now())
        hourly_rate = random_decimal(15, 50)

        employee = Employee(
            employee_id=f"EMP-{i:04d}",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.email() if random.random() > 0.1 else None,
            phone=fake.phone_number() if random.random() > 0.2 else None,
            department=department,
            role=role,
            workstation=workstation,
            hire_date=hire_date,
            hourly_rate=hourly_rate,
            is_active=True
        )
        employees.append(employee)

    Employee.objects.bulk_create(employees)
    print(f"Created {len(employees)} employees")
    return Employee.objects.all()

@transaction.atomic
def create_process_templates(workstations):
    """Create process templates and steps"""
    print("Creating process templates and steps...")
    templates = []

    for i in range(1, NUM_PROCESS_TEMPLATES + 1):
        name = f"Process {fake.word().capitalize()}-{fake.word().capitalize()}"
        template = ProcessTemplate(
            name=name,
            description=fake.text(max_nb_chars=200) if random.random() > 0.3 else None,
            estimated_time=random.randint(30, 480),  # 30 min to 8 hours
            is_active=True
        )
        templates.append(template)

    ProcessTemplate.objects.bulk_create(templates)

    # Create steps for each template
    steps = []
    templates = ProcessTemplate.objects.all()

    for template in tqdm(templates):
        num_steps = random.randint(3, 8)

        for seq in range(1, num_steps + 1):
            workstation_type = random.choice([ws.name.split()[0] for ws in workstations])
            est_time = random.randint(10, 120)  # 10 min to 2 hours

            step = ProcessStep(
                process=template,
                sequence=seq,
                name=f"Step {seq}: {fake.word().capitalize()}",
                description=fake.text(max_nb_chars=100),
                workstation_type=workstation_type,
                 estimated_time=est_time
            )
            steps.append(step)

    ProcessStep.objects.bulk_create(steps)
    print(f"Created {len(templates)} templates with {len(steps)} steps")
    return templates

@transaction.atomic
def create_bills_of_materials(products, templates):
    """Create bills of materials"""
    print("Creating bills of materials...")
    boms = []
    bom_items = []

    # Only create BOMs for finished and WIP products
    finished_products = products.filter(category__in=['FIN', 'WIP'])
    raw_materials = products.filter(category='RAW')

    for product in tqdm(finished_products):
        # Select a random process template
        template = random.choice(templates)

        bom = BillOfMaterials(
            product=product,
            process_template=template,
            description=fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
            version='1.0',
            is_active=True
        )
        boms.append(bom)

    BillOfMaterials.objects.bulk_create(boms)

    # Create BOM items
    boms = BillOfMaterials.objects.all().select_related('process_template', 'product')

    for bom in tqdm(boms):
        # Determine how many components this product needs
        num_components = random.randint(3, 10)
        # Choose random raw materials
        components = random.sample(list(raw_materials), num_components)

        # Get process steps for this BOM's template
        steps = ProcessStep.objects.filter(process=bom.process_template)

        for component in components:
            quantity = random_decimal(0.1, 10, 3)
            unit = random.choice(['units', 'kg', 'liters', 'm', 'sheets'])

            # Randomly assign to a step if steps exist
            step = random.choice(steps) if steps and random.random() > 0.3 else None

            bom_item = BOMItem(
                bom=bom,
                component=component,
                quantity_required=quantity,
                unit_of_measure=unit,
                step=step,
                notes=fake.text(max_nb_chars=100) if random.random() > 0.7 else None
            )
            bom_items.append(bom_item)

    BOMItem.objects.bulk_create(bom_items)
    print(f"Created {len(boms)} BOMs with {len(bom_items)} items")
    return boms

@transaction.atomic
def create_purchase_orders(suppliers, warehouses):
    """Create purchase orders"""
    print("Creating purchase orders...")
    purchase_orders = []
    po_items = []

    # Get supplier products
    supplier_products = SupplierProduct.objects.all().select_related('supplier', 'product')

    # Group supplier_products by supplier for more efficient processing
    supplier_product_map = {}
    for sp in supplier_products:
        if sp.supplier.id not in supplier_product_map:
            supplier_product_map[sp.supplier.id] = []
        supplier_product_map[sp.supplier.id].append(sp)

    current_date = timezone.now().date()
    start_date = current_date - datetime.timedelta(days=365 * YEARS_OF_DATA)

    # Create POs over the time period
    for i in tqdm(range(1, NUM_PURCHASE_ORDERS + 1)):
        # Select a random supplier
        supplier = random.choice(suppliers)
        warehouse = random.choice(warehouses)

        # Generate a random date within the time range
        order_date = random_date(start_date, current_date)
        expected_delivery = order_date + datetime.timedelta(days=random.randint(1, 45))

        # Determine if this PO is in the past or future (relative to current date)
        is_past = order_date < current_date

        # Determine status based on dates
        if is_past:
            if random.random() > 0.1:  # 90% of past POs are received
                status = 'RECEIVED'
                actual_delivery = order_date + datetime.timedelta(days=random.randint(1, 30))
                if actual_delivery > current_date:
                    actual_delivery = current_date
            else:
                status = random.choice(['CANCELLED', 'RECEIVED'])
                actual_delivery = order_date + datetime.timedelta(days=random.randint(1, 30)) if status == 'RECEIVED' else None
                if actual_delivery and actual_delivery > current_date:
                    actual_delivery = current_date
        else:
            status = random.choice(['DRAFT', 'PENDING', 'APPROVED', 'ORDERED'])
            actual_delivery = None

        po = PurchaseOrder(
            po_number=generate_order_number('PO', i),
            supplier=supplier,
            warehouse=warehouse,
            order_date=order_date,
            expected_delivery=expected_delivery,
            actual_delivery=actual_delivery,
            status=status,
            payment_status='PAID' if status == 'RECEIVED' else random.choice(['UNPAID', 'PARTIAL']) if status != 'DRAFT' else 'UNPAID',
            notes=fake.text(max_nb_chars=200)  if random.random() > 0.8 else None,
            created_by=fake.name() if random.random() > 0.5 else None
        )
        purchase_orders.append(po)

    PurchaseOrder.objects.bulk_create(purchase_orders)

    # Create PO items
    purchase_orders = PurchaseOrder.objects.all().select_related('supplier')

    for po in tqdm(purchase_orders):
        # Get products this supplier provides
        if po.supplier.id in supplier_product_map:
            supplier_prods = supplier_product_map[po.supplier.id]

            # If supplier has products, add 1-10 items to the PO
            if supplier_prods:
                num_items = random.randint(1, min(10, len(supplier_prods)))
                po_supplier_prods = random.sample(supplier_prods, num_items)

                total_amount = 0
                for sp in po_supplier_prods:
                    quantity = random.randint(sp.min_order_quantity, sp.min_order_quantity * 10)
                    unit_price = sp.unit_cost

                    # If PO is received, set received quantity
                    if po.status == 'RECEIVED':
                        quantity_received = quantity
                    elif po.status == 'PARTIAL':
                        quantity_received = random.randint(1, quantity - 1)
                    else:
                        quantity_received = 0

                    item = PurchaseOrderItem(
                        purchase_order=po,
                        product=sp.product,
                        quantity_ordered=quantity,
                        quantity_received=quantity_received,
                        unit_price=unit_price,
                        expected_delivery=po.expected_delivery if random.random() > 0.8 else get_future_date(po.order_date)
                    )
                    po_items.append(item)

                    line_total = quantity * unit_price
                    total_amount += line_total

                # Update the PO total amount
                po.total_amount = total_amount

    # Bulk update the PO total amounts
    PurchaseOrder.objects.bulk_update(purchase_orders, ['total_amount'])

    # Create the PO items
    PurchaseOrderItem.objects.bulk_create(po_items)
    print(f"Created {len(purchase_orders)} purchase orders with {len(po_items)} items")

@transaction.atomic
def create_sales_orders(customers, products, warehouses):
    """Create sales orders and associated data"""
    print("Creating sales orders...")
    sales_orders = []
    sales_order_items = []
    invoices = []

    # Filter for finished products only
    finished_products = products.filter(category='FIN')

    current_date = timezone.now().date()
    start_date = current_date - datetime.timedelta(days=365 * YEARS_OF_DATA)

    for i in tqdm(range(1, NUM_SALES_ORDERS + 1)):
        customer = random.choice(customers)
        order_date = random_date(start_date, current_date)
        requested_delivery = order_date + datetime.timedelta(days=random.randint(3, 45))

        # Determine if this is a past or future order
        is_past = order_date < current_date

        # Set status and delivery date based on timing
        if is_past:
            # 80% of past orders are delivered
            if random.random() > 0.2:
                status = 'DELIVERED'
                actual_delivery = requested_delivery + datetime.timedelta(days=random.randint(-7, 14))
                if actual_delivery > current_date:
                    actual_delivery = current_date
            else:
                status = random.choice(['SHIPPED', 'PROCESSING', 'CANCELLED'])
                actual_delivery = None
                if status == 'SHIPPED':
                    actual_delivery = order_date + datetime.timedelta(days=random.randint(2, 10))
                    if actual_delivery > current_date:
                        actual_delivery = None
        else:
            status = random.choice(['DRAFT', 'CONFIRMED', 'PROCESSING'])
            actual_delivery = None

        shipping_cost = random_decimal(10, 200)

        order = SalesOrder(
            order_number=generate_order_number('SO', i),
            customer=customer,
            order_date=order_date,
            requested_delivery=requested_delivery,
            actual_delivery=actual_delivery,
            status=status,
            shipping_method=random.choice(['Standard', 'Express', 'Economy']) if random.random() > 0.2 else None,
            shipping_cost=shipping_cost,
            notes=fake.text(max_nb_chars=200) if random.random() > 0.8 else None,
            created_by=fake.name() if random.random() > 0.5 else None
        )
        sales_orders.append(order)

    SalesOrder.objects.bulk_create(sales_orders)

    # Create sales order items
    sales_orders = SalesOrder.objects.all()

    for order in tqdm(sales_orders):
        # Add 1-5 products to this order
        num_items = random.randint(1, 5)
        order_products = random.sample(list(finished_products), num_items)

        total_amount = 0
        for product in order_products:
            quantity = random.randint(1, 20)
            unit_price = product.unit_price * random_decimal(0.9, 1.2)  # Vary price slightly
            discount = random_decimal(0, 15) if random.random() > 0.7 else 0
            warehouse = random.choice(warehouses)

            item = SalesOrderItem(
                sales_order=order,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                discount_percentage=discount,
                warehouse=warehouse,
                notes=fake.text(max_nb_chars=100) if random.random() > 0.9 else None
            )
            sales_order_items.append(item)

            # Calculate line total with discount
            line_total = quantity * unit_price * decimal.Decimal((1 - discount / 100))
            total_amount += line_total

        # Update total amount and add shipping
        total_amount += order.shipping_cost
        order.total_amount = total_amount

        # Create invoice for completed or shipped orders
        if order.status in ['DELIVERED', 'SHIPPED']:
            due_date = order.order_date + datetime.timedelta(days=30)

            # Determine invoice status
            if order.status == 'DELIVERED' and due_date < current_date:
                if random.random() > 0.15:  # 85% of delivered orders are paid
                    status = 'PAID'
                else:
                    status = 'OVERDUE'
            elif order.status == 'SHIPPED':
                status = random.choice(['ISSUED', 'PARTIAL', 'PAID'])
            else:
                status = 'ISSUED'

           # Ensure vat_rate is a Decimal
            vat_rate = decimal.Decimal(random.choice([5, 8, 23]))  # Convert VAT rate to Decimal
            total_amount = decimal.Decimal("100.00")  # Example total amount

            # Perform calculations with all Decimal values
            net_amount = total_amount / (decimal.Decimal("1") + (vat_rate / decimal.Decimal("100")))  # Convert 1 and 100 to Decimal
            vat_amount = total_amount - net_amount  # VAT amount
            gross_amount = total_amount  # Gross amount remains the same

            payment_method = random.choice(['BANK_TRANSFER', 'CREDIT_CARD', 'CASH', 'PAYPAL', 'OTHER'])

            # Company Details (using Faker to generate company info)
            company_name = fake.company()
            company_address = fake.address()
            company_nip = fake.numerify(text="PL##########")  # Example NIP (Tax ID)
            company_email = fake.company_email()
            company_phone = fake.phone_number()

            invoice = Invoice(
                sales_order=order,
                invoice_number=f"INV-{order.order_number[3:]}",
                issued_date=order.order_date,
                due_date=due_date,
                total_amount=gross_amount,
                status=status,
                vat_rate=vat_rate,
                net_amount=net_amount,
                vat_amount=vat_amount,
                gross_amount=gross_amount,
                payment_method=payment_method,
                company_name=company_name,
                company_address=company_address,
                company_nip=company_nip,
                company_email=company_email,
                company_phone=company_phone,
                notes=fake.text(max_nb_chars=100) if random.random() > 0.9 else None
            )
            invoices.append(invoice)

    # Update the total amounts
    SalesOrder.objects.bulk_update(sales_orders, ['total_amount'])

    # Create the items and invoices
    SalesOrderItem.objects.bulk_create(sales_order_items)
    Invoice.objects.bulk_create(invoices)

    print(f"Created {len(sales_orders)} sales orders with {len(sales_order_items)} items and {len(invoices)} invoices")
    return sales_orders, sales_order_items

@transaction.atomic
def create_manufacturing_orders(products, warehouses, sales_order_items, workstations, employees):
    """Create manufacturing orders and related data"""
    print("Creating manufacturing orders...")
    manufacturing_orders = []
    manufacturing_steps = []
    production_logs = []
    quality_checks = []
    shifts = []

    # Get all BOMs and sales order items
    boms = BillOfMaterials.objects.all().select_related('product', 'process_template')

    # Map products to their BOMs
    product_bom_map = {bom.product.id: bom for bom in boms}

    # Create manufacturing orders both linked to sales orders and independent
    current_date = timezone.now().date()
    start_date = current_date - datetime.timedelta(days=365 * YEARS_OF_DATA)

    # Create some manufacturing orders linked to sales orders
    for i, so_item in enumerate(tqdm(sales_order_items)):
        # Determine if there is a BOM for this product
        if so_item.product.id in product_bom_map:
            bom = product_bom_map[so_item.product.id]
            process_template = bom.process_template
            _num_steps = ProcessStep.objects.filter(process=process_template).count()

            order_date = random_date(start_date, current_date)
            start_date = order_date + datetime.timedelta(days=random.randint(0, 10))
            estimated_completion = start_date + datetime.timedelta(days=random.randint(1, 30))

            # Determine if this order is in the past
            is_past = start_date < current_date

            # Set order status
            if is_past:
                status = 'COMPLETED' if random.random() > 0.2 else random.choice(['IN_PROGRESS', 'ON_HOLD'])
                actual_completion = estimated_completion if status == 'COMPLETED' else None
            else:
                status = random.choice(['DRAFT', 'PLANNED', 'READY'])
                actual_completion = None

            # Create the manufacturing order
            mo = ManufacturingOrder(
                order_number=generate_order_number('MO', i),
                product=so_item.product,
                bom_version=bom.version,
                quantity=so_item.quantity,
                sales_order_item=so_item,
                target_warehouse=random.choice(warehouses),
                status=status,
                priority=random.randint(1, 10),
                start_date=start_date,
                estimated_completion=estimated_completion,
                actual_completion=actual_completion,
                production_cost=random_decimal(1000, 10000),
                notes=fake.text(max_nb_chars=200) if random.random() > 0.8 else None,
                created_by=fake.name() if random.random() > 0.5 else None
            )
            manufacturing_orders.append(mo)

    ManufacturingOrder.objects.bulk_create(manufacturing_orders)

    # Create manufacturing steps for each order
    manufacturing_orders = ManufacturingOrder.objects.all()

    for mo in tqdm(manufacturing_orders):
        if mo.product.id in product_bom_map:
            bom = product_bom_map[mo.product.id]
            steps = ProcessStep.objects.filter(process=bom.process_template)

            for step in steps:
                # Choose a workstation that matches the type needed for this step
                matching_workstations = [
                    ws for ws in workstations if step.workstation_type in ws.name
                ]

                workstation = random.choice(matching_workstations) if matching_workstations else None

                ms = ManufacturingStep(
                    manufacturing_order=mo,
                    process_step=step,
                    sequence=step.sequence,
                    name=step.name,
                    description=step.description,
                    workstation=workstation,
                    status=random.choice(['PENDING', 'IN_PROGRESS', 'COMPLETED']),
                    scheduled_start=mo.start_date + datetime.timedelta(days=random.randint(0, 5)),
                    scheduled_end=mo.estimated_completion - datetime.timedelta(days=random.randint(0, 5)),
                    actual_start=mo.start_date if mo.status == 'IN_PROGRESS' else None,
                    actual_end=mo.estimated_completion if mo.status == 'COMPLETED' else None
                )
                manufacturing_steps.append(ms)

    ManufacturingStep.objects.bulk_create(manufacturing_steps)

    # Create production logs and quality checks
    for step in tqdm(manufacturing_steps):
        # Create a production log for each manufacturing step
        log = ProductionLog(
            manufacturing_order=step.manufacturing_order,
            manufacturing_step=step,
            workstation=step.workstation,
            date=step.scheduled_start if step.scheduled_start else current_date,
            start_time=datetime.time(9, 0) if isinstance(step.scheduled_start, datetime.date) else step.scheduled_start.time(),
            end_time=datetime.time(17, 0) if isinstance(step.scheduled_end, datetime.date) else (step.scheduled_end.time() if step.scheduled_end else None),
            units_produced=random.randint(1, step.manufacturing_order.quantity),
            units_defective=random.randint(0, 5),
            downtime_minutes=random.randint(0, 60),
            downtime_reason=fake.text(max_nb_chars=100) if random.random() > 0.3 else None,
            remarks=fake.text(max_nb_chars=100) if random.random() > 0.3 else None,
            created_by=fake.name() if random.random() > 0.5 else None
        )
        production_logs.append(log)

        # Create a quality check for each production log
        qc = QualityCheck(
            production_log=log,
            check_type=random.choice(['Visual', 'Dimensional', 'Functional']),
            result=random.choice(['PASS', 'FAIL', 'WARNING']),
            measurement=f"{random_decimal(0.1, 10)} units" if random.random() > 0.5 else None,
            notes=fake.text(max_nb_chars=100) if random.random() > 0.7 else None,
            checked_by=fake.name(),
            checked_at=timezone.now()
        )
        quality_checks.append(qc)

    ProductionLog.objects.bulk_create(production_logs)
    QualityCheck.objects.bulk_create(quality_checks)

    # Create employee shifts for each manufacturing step
    for step in tqdm(manufacturing_steps):
        # Select a random employee for this shift
        employee = random.choice(employees)

        shift = Shift(
            employee=employee,
            manufacturing_order=step.manufacturing_order,
            manufacturing_step=step,
            workstation=step.workstation,
            shift_date=step.scheduled_start if step.scheduled_start else current_date,
            shift_type=random.choice(['MORNING', 'AFTERNOON', 'NIGHT']),
            start_time=datetime.time(9, 0) if isinstance(step.scheduled_start, datetime.date) else step.scheduled_start.time(),
            end_time=datetime.time(17, 0) if isinstance(step.scheduled_end, datetime.date) else (step.scheduled_end.time() if step.scheduled_end else None),
            break_minutes=random.randint(15, 60),
            overtime_minutes=random.randint(0, 120),
            status=random.choice(['SCHEDULED', 'IN_PROGRESS', 'COMPLETED']),
            notes=fake.text(max_nb_chars=100) if random.random() > 0.7 else None
        )
        shifts.append(shift)

    Shift.objects.bulk_create(shifts)

    print(f"Created {len(manufacturing_orders)} manufacturing orders, {len(manufacturing_steps)} steps, {len(production_logs)} logs, {len(quality_checks)} quality checks, and {len(shifts)} shifts")

def clear_database():
    """Clear all records from the database"""
    print("Clearing database...")
    models = [
        Warehouse, Product, ProductInventory, Supplier, SupplierProduct, PurchaseOrder, PurchaseOrderItem,
        Customer, SalesOrder, SalesOrderItem, Invoice, Workstation, ProcessTemplate, ProcessStep,
        BillOfMaterials, BOMItem, ManufacturingOrder, ManufacturingStep, ProductionLog, QualityCheck,
        Employee, Shift, MaintenanceSchedule, MaintenanceActivity, ProductionKPI
    ]

    for model in models:
        model.objects.all().delete()

    print("Database cleared")


class Command(BaseCommand):
    help = 'Populate the ERP database with sample data'

    def handle(self, *args, **kwargs):
        clear_database()
        createsuperuser()
        create_order_number()
        warehouses = create_warehouses()
        products = create_products(warehouses)
        suppliers = create_suppliers()
        create_supplier_products(suppliers, products)
        customers = create_customers()
        workstations = create_workstations()
        employees = create_employees(workstations)
        templates = create_process_templates(workstations)
        _boms = create_bills_of_materials(products, templates)
        create_purchase_orders(suppliers, warehouses)
        sales_orders, sales_order_items = create_sales_orders(customers, products, warehouses)
        create_manufacturing_orders(products, warehouses, sales_order_items, workstations, employees)
