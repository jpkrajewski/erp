# Generated by Django 5.1.6 on 2025-03-05 20:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("erp", "0006_alter_supplier_phone"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customer",
            name="phone",
            field=models.CharField(max_length=25),
        ),
    ]
