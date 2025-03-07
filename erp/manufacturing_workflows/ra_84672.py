import logging

from django.db import transaction

from erp.models import (
    ManufacturingOrder,
    ManufacturingStep,
    ManufacturingStepInput,
    Workstation,
)

logger = logging.getLogger(__name__)


def ra_84672(instance: ManufacturingOrder):
    """Create a workflow for a new manufacturing order"""
    with transaction.atomic():
        # Find a workstations
        assembler_frame = Workstation.objects.ready_for_production(
            "Frame Assembly"
        ).first()
        assembler_wheels = Workstation.objects.ready_for_production(
            "Wheel Assembly"
        ).first()
        assembler_seat = Workstation.objects.ready_for_production(
            "Seat Assembly"
        ).first()
        assembler_handlebars = Workstation.objects.ready_for_production(
            "Handlebars Assembly"
        ).first()

        steps = ManufacturingStep.from_list(
            instance,
            [
                ManufacturingStepInput(
                    name="Frame Assembly",
                    workstation=assembler_frame,
                    description="Assemble the frame of the bike",
                ),
                ManufacturingStepInput(
                    name="Wheel Assembly",
                    workstation=assembler_wheels,
                    description="Assemble the wheels of the bike",
                ),
                ManufacturingStepInput(
                    name="Seat Assembly",
                    workstation=assembler_seat,
                    description="Assemble the seat of the bike",
                ),
                ManufacturingStepInput(
                    name="Handlebars Assembly",
                    workstation=assembler_handlebars,
                    description="Assemble the handlebars of the bike",
                ),
            ],
        )

        ManufacturingStep.objects.bulk_create(steps)
        logger.info(f"Created manufacturing steps for order {instance}")

        instance.status = "PLANNED"
        instance.save()
        logger.info(f"Updated status of order {instance} to PLANNED")
