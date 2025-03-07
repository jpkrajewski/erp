from typing import Callable, Mapping

from erp.models import ManufacturingOrder

from .ra_84672 import ra_84672

MANUFACTURING_WORKFLOWS: Mapping[str, Callable[[ManufacturingOrder], str]] = {
    "RA-84672": ra_84672,
}

__all__ = ["MANUFACTURING_WORKFLOWS"]
