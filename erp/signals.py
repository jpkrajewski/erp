from erp.models import Product, ProductInventory
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging


logger = logging.getLogger(__name__)
