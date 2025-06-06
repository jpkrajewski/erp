# Generated by Django 5.1.6 on 2025-03-03 18:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("erp", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CurrencyRate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("currency_code", models.CharField(max_length=3, unique=True)),
                ("exchange_rate", models.DecimalField(decimal_places=6, max_digits=20)),
                ("last_updated", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
