import logging

from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from erp.enums import EmployeeRole
from erp.manufacturing_workflows import MANUFACTURING_WORKFLOWS
from erp.models import Employee, ManufacturingOrder, QualityCheck
from erp.tasks import invoice_generate_pdf, send_email_generic

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


@receiver(post_save, sender=ManufacturingOrder)
def create_manufacturing_order_workflow(
    sender, instance: ManufacturingOrder, created: bool, **kwargs
):
    """Create a workflow for a new manufacturing order"""
    if created and instance.status == "READY":
        # "RA-84672" ect...
        if instance.product.sku not in MANUFACTURING_WORKFLOWS:
            logger.debug(
                f"Manufacturing workflow not found for product {instance.product.sku}"
            )
            return

        result = MANUFACTURING_WORKFLOWS[instance.product.sku](instance)
        logger.info(f"Created workflow for order {instance}, result: {result}")


def send_order_status_email(subject: str, body: str, recipients: list):
    """Helper function to send an email notification for order status changes."""
    try:
        # Use Celery to send the email asynchronously
        send_email_generic.delay(subject, body, recipients)
        logger.info(f"Email sent successfully. Subject: '{subject}', Recipients: {recipients}")
    except Exception as e:
        logger.error(f"Failed to send email for subject '{subject}': {e}")


@receiver(post_save, sender=ManufacturingOrder)
def send_email_when_manufacturing_order_is_completed_or_canceled(
    sender, instance: ManufacturingOrder, created: bool, **kwargs
):
    """Send an email when a manufacturing order is completed or canceled."""
    if not created:
        # Define common email body template and subject
        recipients = ["example@example.com"]  # Add actual recipients, e.g., managers, users
        if instance.status == "COMPLETED":
            subject = "Manufacturing Order Completed"
            body = f"Order {instance.order_number} has been completed successfully."
            send_order_status_email(subject, body, recipients)
        elif instance.status == "CANCELED":
            subject = "Manufacturing Order Canceled"
            body = f"Order {instance.order_number} has been canceled."
            send_order_status_email(subject, body, recipients)
        else:
            logger.info(f"Order {instance.order_number} status updated to {instance.status}, no email sent.")


def invoice_when_created_or_updated_generate_pdf(sender, instance, created, **kwargs):
    """Generate a PDF when an invoice is created or updated."""
    if created:
        invoice_generate_pdf.delay(instance)
        logger.info(f"PDF generated for invoice {instance.invoice_number}")
