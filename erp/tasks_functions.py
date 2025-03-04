import requests
from erp.models import CurrencyRate

def send_emails_when_product_stock_is_below_minimum():
    products = (
        instance
        .values("product__id", "product__name", "product__min_stock_level")
        .annotate(total_quantity=Sum("quantity"))
        .filter(total_quantity__lt=F("product__min_stock_level"))
    )
    if not products:
        return "All products have stock above minimum level"
    
    for product in products:
        logger.info(f"Product {product['product__name']} has stock below minimum level.")
        # Send an email to the store manager
        # send_email(
        #     subject=f"Product {product['product__name']} has stock below minimum level",
        #     message=f"Product {product['product__name']} has stock below minimum level. "
        #             f"Current stock: {product['total_quantity']}. "
        #             f"Minimum stock level: {product['product__min_stock_level']}."
        # )


def get_currency_exchange_rates_and_update_currency():
    api = "https://open.er-api.com/v6/latest/USD"
    response = requests.get(api)
    data = response.json()
    rates = data["rates"]
    CurrencyRate.objects.all().delete()
    CurrencyRate.objects.bulk_create(
        [
            CurrencyRate(
                currency_code=currency,
                exchange_rate=rate
            )
            for currency, rate in rates.items()
        ],
    )