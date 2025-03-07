from django.db.models import signals
from django.test import TestCase

from erp.manufacturing_workflows import MANUFACTURING_WORKFLOWS
from erp.models import ManufacturingOrder, ManufacturingStep, Product, Workstation
from erp.signals import create_manufacturing_order_workflow


class TestManufacturingWorkflows(TestCase):
    def setUp(self):
        # Create a product that should trigger the RA-84672 workflow.
        self.product = Product.objects.create(
            name="Bicycle",
            sku="RA-84672",
            description="A two-wheeled mode of transportation",
            unit_price=1000,
        )
        # Create all required workstations for the workflow.
        self.workstation_frame = Workstation.objects.create(
            name="Frame Assembly",
            machine_id="FA001",
            location="Factory A",
            description="Assemble the frame of the bike",
            status="OPERATIONAL",
            is_active=True,
        )
        self.workstation_wheels = Workstation.objects.create(
            name="Wheel Assembly",
            machine_id="WA001",
            location="Factory A",
            description="Assemble the wheels of the bike",
            status="OPERATIONAL",
            is_active=True,
        )
        self.workstation_seat = Workstation.objects.create(
            name="Seat Assembly",
            machine_id="SA001",
            location="Factory A",
            description="Assemble the seat of the bike",
            status="OPERATIONAL",
            is_active=True,
        )
        self.workstation_handlebars = Workstation.objects.create(
            name="Handlebars Assembly",
            machine_id="HA001",
            location="Factory A",
            description="Assemble the handlebars of the bike",
            status="OPERATIONAL",
            is_active=True,
        )

    def test_ra_84672_workflow_creation(self):
        signals.post_save.disconnect(
            receiver=create_manufacturing_order_workflow, sender=ManufacturingOrder
        )
        """
        Test that a manufacturing order with SKU 'RA-84672' and status 'READY' triggers
        the correct workflow, creating 4 manufacturing steps with the expected details,
        and updates the order's status to 'PLANNED'.
        """
        # Create a manufacturing order that should trigger the workflow.
        order = ManufacturingOrder.objects.create(
            product=self.product,
            quantity=1,
            status="READY",
            start_date="2021-01-01",
            estimated_completion="2021-01-10",
        )

        # Execute the workflow function via the MANUFACTURING_WORKFLOWS registry.
        MANUFACTURING_WORKFLOWS.get(self.product.sku)(order)

        # Refresh the order from the database.
        order.refresh_from_db()

        # Retrieve all manufacturing steps created for this order.
        steps = ManufacturingStep.objects.filter(manufacturing_order=order)
        self.assertEqual(
            steps.count(), 4, "Expected 4 manufacturing steps to be created."
        )

        # Define the expected details for each manufacturing step.
        expected_steps = [
            {
                "name": "Frame Assembly",
                "description": "Assemble the frame of the bike",
                "workstation": self.workstation_frame,
            },
            {
                "name": "Wheel Assembly",
                "description": "Assemble the wheels of the bike",
                "workstation": self.workstation_wheels,
            },
            {
                "name": "Seat Assembly",
                "description": "Assemble the seat of the bike",
                "workstation": self.workstation_seat,
            },
            {
                "name": "Handlebars Assembly",
                "description": "Assemble the handlebars of the bike",
                "workstation": self.workstation_handlebars,
            },
        ]

        # Verify that each expected step exists and has the correct attributes.
        for expected in expected_steps:
            step = steps.get(name=expected["name"])
            self.assertEqual(
                step.description,
                expected["description"],
                f"Mismatch in description for step '{expected['name']}'",
            )
            self.assertEqual(
                step.workstation,
                expected["workstation"],
                f"Mismatch in workstation for step '{expected['name']}'",
            )

        # Confirm that the order status has been updated to 'PLANNED'
        self.assertEqual(
            order.status,
            "PLANNED",
            "Manufacturing order status should be updated to PLANNED.",
        )
