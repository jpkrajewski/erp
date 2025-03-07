import logging

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from erp.invoices.generators import generate_invoice
from erp.models import Invoice
from erp.tasks_functions import (
    get_currency_exchange_rates_and_update_currency,
    send_emails_when_product_stock_is_below_minimum,
)

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


@shared_task
def send_email_generic(subject, message, recipient_list):
    send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)
    return "Email sent successfully"


@shared_task
def invoice_generate_pdf(instance: Invoice):
    generate_invoice(instance)
