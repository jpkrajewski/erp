import logging

import requests
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F, Sum

from erp.enums import EmployeeRole
from erp.models import CurrencyRate, Employee, ProductInventory

logger = logging.getLogger(__name__)


def send_emails_when_product_stock_is_below_minimum():
    """Send alerts if product stock falls below the minimum level."""

    # Get products with low stock
    low_stock_products = (
        ProductInventory.objects.values(
            "product__id", "product__name", "product__min_stock_level"
        )
        .annotate(total_quantity=Sum("quantity"))
        .filter(total_quantity__lt=F("product__min_stock_level"))
    )

    if not low_stock_products.exists():
        return "✅ All products have stock above the minimum level."

    # Fetch emails of team leads
    team_leads = Employee.objects.filter(role=EmployeeRole.TEAM_LEAD).values_list(
        "email", flat=True
    )

    if not team_leads:
        logger.warning("⚠️ No team leads found to notify.")
        return "⚠️ No team leads found to notify."

    # Format product details for the email message
    product_list = "\n".join(
        f"- {product['product__name']} (Stock: {product['total_quantity']}, Min: {product['product__min_stock_level']})"
        for product in low_stock_products
    )

    email_body = f"🚨 The following products are below the minimum stock level:\n\n{product_list}"

    # Send notification email
    send_mail(
        subject="🔴 Product Stock Alert: Below Minimum Level",
        message=email_body,
        from_email="no-reply@erp.com",
        recipient_list=list(team_leads),
    )

    # Log the alert for each product
    for product in low_stock_products:
        logger.info(
            f"⚠️ Product {product['product__name']} is below the minimum stock level."
        )

    return "📩 Stock alert email sent successfully."


def get_currency_exchange_rates_and_update_currency():
    api = "https://open.er-api.com/v6/latest/USD"
    response = requests.get(api)
    data = response.json()
    rates = data["rates"]
    with transaction.atomic():
        CurrencyRate.objects.all().delete()
        CurrencyRate.objects.bulk_create(
            [
                CurrencyRate(currency_code=currency, exchange_rate=rate)
                for currency, rate in rates.items()
            ],
        )
