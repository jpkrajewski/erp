from django.test import TestCase
from erp.tasks_functions import get_currency_exchange_rates_and_update_currency, send_emails_when_product_stock_is_below_minimum
from erp.models import CurrencyRate
from unittest.mock import patch
from decimal import Decimal


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
            }
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
        self.assertEqual(usd_rate.exchange_rate, Decimal('1.0'))

        eur_rate = CurrencyRate.objects.get(currency_code="EUR")
        self.assertAlmostEqual(eur_rate.exchange_rate, Decimal('0.96146'), places=5)

        gbp_rate = CurrencyRate.objects.get(currency_code="GBP")
        self.assertAlmostEqual(gbp_rate.exchange_rate, Decimal('0.793844'), places=5)

        # Optionally, assert that the expected number of records exists
        self.assertEqual(CurrencyRate.objects.count(), len(self.payload['rates']))