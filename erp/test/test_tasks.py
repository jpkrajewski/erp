from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings

from erp.enums import EmployeeRole
from erp.models import CurrencyRate, Employee, Product, ProductInventory, Warehouse
from erp.tasks_functions import (
    get_currency_exchange_rates_and_update_currency,
    send_emails_when_product_stock_is_below_minimum,
)


class TestUpdateCurrencyExchangeRates(TestCase):
    def setUp(self):
        CurrencyRate.objects.create(currency_code="USD", exchange_rate=1.0)
        CurrencyRate.objects.create(currency_code="EUR", exchange_rate=0.85)
        CurrencyRate.objects.create(currency_code="GBP", exchange_rate=0.75)

        self.payload = {
            "result": "success",
            "provider": "https://www.exchangerate-api.com",
            "documentation": "https://www.exchangerate-api.com/docs/free",
            "terms_of_use": "https://www.exchangerate-api.com/terms",
            "time_last_update_unix": 1740960152,
            "time_last_update_utc": "Mon, 03 Mar 2025 00:02:32 +0000",
            "time_next_update_unix": 1741048062,
            "time_next_update_utc": "Tue, 04 Mar 2025 00:27:42 +0000",
            "time_eol_unix": 0,
            "base_code": "USD",
            "rates": {
                "USD": 1,
                "EUR": 0.96146,
                "GBP": 0.793844,
            },
        }

    @patch("erp.tasks_functions.requests.get")
    def test_get_currency_exchange_rates_and_update_currency(self, mock_get):
        # Arrange
        response = mock_get.return_value
        response.json.return_value = self.payload
        # Act
        get_currency_exchange_rates_and_update_currency()

        # Assert
        usd_rate = CurrencyRate.objects.get(currency_code="USD")
        self.assertEqual(usd_rate.exchange_rate, Decimal("1.0"))

        eur_rate = CurrencyRate.objects.get(currency_code="EUR")
        self.assertAlmostEqual(eur_rate.exchange_rate, Decimal("0.96146"), places=5)

        gbp_rate = CurrencyRate.objects.get(currency_code="GBP")
        self.assertAlmostEqual(gbp_rate.exchange_rate, Decimal("0.793844"), places=5)

        # Optionally, assert that the expected number of records exists
        self.assertEqual(CurrencyRate.objects.count(), len(self.payload["rates"]))


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TestSendMailWhenProductStockIsLow(TestCase):
    def setUp(self):
        mail.outbox = []

        Employee.objects.create(email="test@test.com", role=EmployeeRole.TEAM_LEAD)
        # Create a Warehouse
        self.warehouse = Warehouse.objects.create(name="Main Warehouse", capacity=1000)

        # Create Products
        self.product1 = Product.objects.create(
            name="Product 1", min_stock_level=10, unit_price=100, sku="SKU1"
        )
        self.product2 = Product.objects.create(
            name="Product 2", min_stock_level=5, unit_price=200, sku="SKU2"
        )

        # Create ProductInventory (Stock is Above Minimum)
        ProductInventory.objects.create(
            product=self.product1, warehouse=self.warehouse, quantity=15
        )

        # Create ProductInventory (Stock is Below Minimum)
        ProductInventory.objects.create(
            product=self.product2, warehouse=self.warehouse, quantity=2
        )

    def test_stock_above_minimum_no_email_sent(self):
        """Test that no email is sent if stock is above minimum"""
        ProductInventory.objects.filter(product=self.product2).update(
            quantity=15
        )  # Stock above minimum

        task_message = send_emails_when_product_stock_is_below_minimum()

        self.assertEqual(
            task_message, "✅ All products have stock above the minimum level."
        )
        self.assertEqual(len(mail.outbox), 0)  # No email should be sent

    def test_stock_below_minimum_email_sent(self):
        """Test that an email is sent if stock is below minimum"""
        ProductInventory.objects.filter(product=self.product2).update(
            quantity=2
        )  # Stock below minimum

        send_emails_when_product_stock_is_below_minimum()

        self.assertEqual(len(mail.outbox), 1)  # At least one email should be sent
        self.assertIn(
            "🔴 Product Stock Alert: Below Minimum Level", mail.outbox[0].subject
        )
