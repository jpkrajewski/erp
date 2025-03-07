from django.test import TestCase

from erp.invoices.generators import generate_invoice
from erp.models import Invoice


class InvoiceGenerationTest(TestCase):

    def setUp(self):
        # Create a sample invoice for testing
        self.invoice = Invoice.objects.create(
            invoice_number="INV-12345",
            company_name="Test Company",
            company_address="**********************",
            company_phone="123456789",
            company_email="test@example.com",
            company_nip="1234567890",
            customer_name="John Doe",
            customer_address="*******************************",
            customer_email="john.doe@example.com",
            customer_phone="987654321",
            issued_date="2023-10-01",
            due_date="2023-11-01",
            payment_method="BANK_TRANSFER",
            net_amount=1000.00,
            vat_rate=23.00,
            vat_amount=230.00,
            gross_amount=1230.00,
            total_amount=1230.00,
            notes="Thank you for your business.",
        )

    def test_generate_invoice(self):
        # Generate the invoice HTML
        rendered_html = generate_invoice(self.invoice)

        # Perform assertions to check for expected content
        self.assertIn("Invoice Number: INV-12345", rendered_html)
        self.assertIn("Test Company", rendered_html)
        self.assertIn("John Doe", rendered_html)
        self.assertIn("Bank Transfer", rendered_html)
        self.assertIn("Issued", rendered_html)
        self.assertIn("Thank you for your business.", rendered_html)
