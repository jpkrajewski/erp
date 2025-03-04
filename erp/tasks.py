from erp.models import ProductInventory
from django.db.models import Sum, F
import logging
from celery import shared_task
from erp.models import CurrencyRate
import requests
from erp.tasks_functions import get_currency_exchange_rates_and_update_currency, send_emails_when_product_stock_is_below_minimum

logger = logging.getLogger(__name__)


@shared_task
def check_if_product_stock_is_below_minimum():
    send_emails_when_product_stock_is_below_minimum()
    return "Sending email to manager"

@shared_task(
    autoretry_for=(KeyError, requests.exceptions.RequestException),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
)
def update_currency_exchange_rates():
    get_currency_exchange_rates_and_update_currency()
    return "Currency exchange rates updated successfully"