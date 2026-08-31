from __future__ import annotations

from dataclasses import dataclass

from .paths import APP_NAME


PRODUCT_NAME = APP_NAME
LICENSE_TYPE = "GNU AGPL v3.0 or later"


@dataclass(frozen=True)
class LicenseStatus:
    """Información de licencia mostrada por la interfaz.

    Manualtech ya no utiliza activación, seriales, identificadores de equipo ni
    caducidad. Esta clase se conserva únicamente para mantener una interfaz
    estable con la ventana principal y mostrar el estado open source.
    """

    product: str = PRODUCT_NAME
    license_type: str = LICENSE_TYPE
    active: bool = True
    activated_at: str = ""
    expires_at: str = ""
    valid_days: int = 0
    days_remaining: str = "No aplica"
    reason: str = "open_source"

    @property
    def state_label(self) -> str:
        return "Open source"

    @property
    def blocking_message(self) -> str:
        return ""

    @property
    def activated_at_label(self) -> str:
        return "No aplica"

    @property
    def expires_at_label(self) -> str:
        return "Sin caducidad"
