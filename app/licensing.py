from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import platform
import secrets
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .paths import APP_NAME, resource_path


PRODUCT_NAME = APP_NAME
LICENSE_TYPE = "Personal"
LICENSE_FILENAME = "license.json"
SERIAL_PREFIX = "MT"
SERIAL_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
SERIAL_SECRET = b"Manualtech-MSL-Beta-2026-local-activation"
SERIAL_BODY_LENGTH = 12
SERIAL_CHECKSUM_LENGTH = 4


@dataclass(frozen=True)
class LicenseStatus:
    product: str = PRODUCT_NAME
    license_type: str = LICENSE_TYPE
    active: bool = False
    activated_at: str = ""

    @property
    def state_label(self) -> str:
        return "Activado" if self.active else "No activado"


def normalize_serial(serial: str) -> str:
    cleaned = serial.strip().upper().replace(" ", "")
    parts = [part for part in cleaned.split("-") if part]
    if parts and parts[0] == SERIAL_PREFIX:
        body = "".join(parts[1:])
        return f"{SERIAL_PREFIX}-" + "-".join(
            body[index : index + 4] for index in range(0, len(body), 4)
        )
    return cleaned


def _serial_body(serial: str) -> str:
    normalized = normalize_serial(serial)
    if not normalized.startswith(f"{SERIAL_PREFIX}-"):
        return ""
    body = normalized[len(SERIAL_PREFIX) + 1 :].replace("-", "")
    if len(body) != SERIAL_BODY_LENGTH + SERIAL_CHECKSUM_LENGTH:
        return ""
    if any(char not in SERIAL_ALPHABET for char in body):
        return ""
    groups = normalized.split("-")
    if len(groups) != 5 or any(len(group) != 4 for group in groups[1:]):
        return ""
    return body


def _checksum(payload: str) -> str:
    digest = hmac.new(
        SERIAL_SECRET,
        payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    value = int.from_bytes(digest[:8], "big")
    chars: list[str] = []
    for _ in range(SERIAL_CHECKSUM_LENGTH):
        chars.append(SERIAL_ALPHABET[value % len(SERIAL_ALPHABET)])
        value //= len(SERIAL_ALPHABET)
    return "".join(chars)


def validate_serial(serial: str) -> bool:
    body = _serial_body(serial)
    if not body:
        return False
    payload = body[:SERIAL_BODY_LENGTH]
    provided_checksum = body[SERIAL_BODY_LENGTH:]
    return hmac.compare_digest(provided_checksum, _checksum(payload))


def generate_serial() -> str:
    payload = "".join(secrets.choice(SERIAL_ALPHABET) for _ in range(SERIAL_BODY_LENGTH))
    body = payload + _checksum(payload)
    return f"{SERIAL_PREFIX}-" + "-".join(
        body[index : index + 4] for index in range(0, len(body), 4)
    )


def generate_serials(quantity: int) -> list[str]:
    if quantity < 1:
        raise ValueError("La cantidad debe ser 1 o superior.")
    return [generate_serial() for _ in range(quantity)]


def activation_hash(serial: str) -> str:
    normalized = normalize_serial(serial)
    machine_hint = f"{platform.node()}|{Path.home()}"
    return hmac.new(
        SERIAL_SECRET,
        f"{PRODUCT_NAME}|{LICENSE_TYPE}|{normalized}|{machine_hint}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def integrity_hash(payload: dict[str, str]) -> str:
    signed_payload = "|".join(
        [
            payload.get("producto", ""),
            payload.get("tipo_licencia", ""),
            payload.get("estado", ""),
            payload.get("hash_validacion", ""),
            payload.get("fecha_activacion", ""),
        ]
    )
    return hmac.new(
        SERIAL_SECRET,
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class LicenseManager:
    def __init__(self, data_root: Path) -> None:
        self.data_root = Path(data_root)
        self.license_path = self.data_root / LICENSE_FILENAME

    def status(self) -> LicenseStatus:
        try:
            payload = json.loads(self.license_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return LicenseStatus()

        expected_integrity = integrity_hash(payload)
        if not hmac.compare_digest(payload.get("integridad", ""), expected_integrity):
            return LicenseStatus()

        is_active = (
            payload.get("producto") == PRODUCT_NAME
            and payload.get("tipo_licencia") == LICENSE_TYPE
            and payload.get("estado") == "activado"
            and bool(payload.get("hash_validacion"))
        )
        return LicenseStatus(
            product=payload.get("producto", PRODUCT_NAME),
            license_type=payload.get("tipo_licencia", LICENSE_TYPE),
            active=is_active,
            activated_at=payload.get("fecha_activacion", ""),
        )

    def is_activated(self) -> bool:
        return self.status().active

    def activate(self, serial: str) -> bool:
        if not validate_serial(serial):
            return False

        payload = {
            "producto": PRODUCT_NAME,
            "tipo_licencia": LICENSE_TYPE,
            "estado": "activado",
            "hash_validacion": activation_hash(serial),
            "fecha_activacion": datetime.now().isoformat(timespec="seconds"),
        }
        payload["integridad"] = integrity_hash(payload)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.license_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True


class ActivationDialog(QDialog):
    def __init__(self, license_manager: LicenseManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.license_manager = license_manager
        self.setWindowTitle("Activación de Manualtech")
        self.setMinimumWidth(440)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        logo_path = resource_path("assets", "manualtech_logo.png")
        header = QHBoxLayout()
        if logo_path.exists():
            logo = QLabel()
            pixmap = QPixmap(str(logo_path)).scaled(
                72,
                72,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo.setPixmap(pixmap)
            logo.setFixedSize(76, 76)
            header.addWidget(logo)

        title = QLabel("<b>Manualtech</b><br>Introduce tu clave de activación")
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setWordWrap(True)
        header.addWidget(title, 1)
        layout.addLayout(header)

        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("MT-XXXX-XXXX-XXXX-XXXX")
        self.serial_edit.setMaxLength(22)
        self.serial_edit.returnPressed.connect(self._activate)
        layout.addWidget(self.serial_edit)

        help_text = QLabel("Si no tienes una clave, contacta con info@motorsuitelab.com")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.activate_button = QPushButton("Activar")
        self.exit_button = QPushButton("Salir")
        self.activate_button.clicked.connect(self._activate)
        self.exit_button.clicked.connect(self.reject)
        buttons.addWidget(self.activate_button)
        buttons.addWidget(self.exit_button)
        layout.addLayout(buttons)

        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

    def _activate(self) -> None:
        serial = self.serial_edit.text().strip()
        if not validate_serial(serial):
            QMessageBox.warning(self, "Activación", "Clave de activación no válida.")
            return

        try:
            self.license_manager.activate(serial)
        except OSError:
            QMessageBox.critical(self, "Activación", "No se pudo guardar la activación.")
            return

        QMessageBox.information(self, "Activación", "Manualtech activado correctamente.")
        self.accept()


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Genera seriales válidos de Manualtech.")
    parser.add_argument(
        "--cantidad",
        type=int,
        default=1,
        help="Número de seriales a generar.",
    )
    args = parser.parse_args()
    for serial in generate_serials(args.cantidad):
        print(serial)
    return 0
