import logging

from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from erp.enums import EmployeeRole
from erp.models import Employee, QualityCheck

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Employee)
def user_set_permissions(sender, instance, created, **kwargs):
    """Set user permissions based on employee role"""
    if created:
        try:
            user = instance.user
            if instance.role == EmployeeRole.QUALITY_INSPECTOR:
                content_type = ContentType.objects.get_for_model(QualityCheck)
                permission = Permission.objects.get(
                    codename="change_qualitycheck",
                    content_type=content_type,
                )
                permission2 = Permission.objects.get(
                    codename="view_qualitycheck",
                    content_type=content_type,
                )
                permission3 = Permission.objects.get(
                    codename="add_qualitycheck",
                    content_type=content_type,
                )
                permission4 = Permission.objects.get(
                    codename="delete_qualitycheck",
                    content_type=content_type,
                )
                user.user_permissions.add(
                    permission, permission2, permission3, permission4
                )

        except User.DoesNotExist:
            logger.error(f"User does not exist for employee {instance}")
            return
