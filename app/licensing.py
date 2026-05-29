from __future__ import annotations

import argparse
import getpass
import hashlib
import hmac
import json
import logging
import math
import os
import platform
import secrets
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


logger = logging.getLogger(__name__)

PRODUCT_NAME = APP_NAME
APP_VERSION = "1.0.0-beta"
LICENSE_TYPE = "Beta 30 días"
LICENSE_FILENAME = "license.json"
VALID_DAYS = 30
ACTIVATION_URL = os.environ.get(
    "MANUALTECH_ACTIVATION_URL",
    "https://www.motorsuitelab.com/api/manualtech/activate",
)

SERIAL_PREFIX = "MT"
SERIAL_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
SERIAL_SECRET = b"Manualtech-MSL-Beta-2026-local-activation"
SERIAL_HASH_SECRET = b"Manualtech-MSL-Beta-2026-serial-hash"
SERIAL_BODY_LENGTH = 12
SERIAL_CHECKSUM_LENGTH = 4

MACHINE_ID_SALT = "Manualtech-MSL-machine-id-v1"

# Protección temporal para la beta. En una versión comercial final conviene
# cambiar esto por firma asimétrica: servidor firma con clave privada y la app
# verifica con una clave pública embebida.
LICENSE_SIGNATURE_SECRET = b"Manualtech-MSL-Beta-2026-license-signature"


@dataclass(frozen=True)
class LicenseStatus:
    product: str = PRODUCT_NAME
    license_type: str = LICENSE_TYPE
    active: bool = False
    activated_at: str = ""
    expires_at: str = ""
    valid_days: int = VALID_DAYS
    days_remaining: int = 0
    reason: str = "no_license"

    @property
    def state_label(self) -> str:
        if self.active:
            return "Activado"
        if self.reason == "expired":
            return "Caducado"
        return "No activado"

    @property
    def blocking_message(self) -> str:
        if self.reason == "expired":
            return (
                "La licencia Beta de Manualtech ha caducado. Contacta con "
                "info@motorsuitelab.com para renovar o adquirir una licencia."
            )
        if self.reason == "machine_mismatch":
            return "Esta licencia no corresponde a este equipo."
        if self.reason in {"invalid_signature", "invalid_payload", "read_error"}:
            return "La licencia local no es válida."
        return ""

    @property
    def activated_at_label(self) -> str:
        return _format_datetime(self.activated_at) if self.activated_at else "No disponible"

    @property
    def expires_at_label(self) -> str:
        return _format_datetime(self.expires_at) if self.expires_at else "No disponible"


@dataclass(frozen=True)
class ActivationResult:
    ok: bool
    message: str


def _short_hash(value: str, length: int = 8) -> str:
    if not value:
        return ""
    return f"{value[:length]}..."


def _mask_serial(serial: str) -> str:
    normalized = normalize_serial(serial)
    parts = normalized.split("-")
    if len(parts) == 5:
        return "-".join([parts[0], parts[1], "****", "****", "****"])
    if len(normalized) > 6:
        return f"{normalized[:6]}..."
    return "***"


def _redact_activation_payload(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if key == "serial":
                redacted[key] = _mask_serial(str(item))
            elif key in {"serial_hash", "machine_id_hash", "signature"}:
                redacted[key] = _short_hash(str(item))
            elif key == "license":
                redacted[key] = _redact_activation_payload(item)
            else:
                redacted[key] = _redact_activation_payload(item)
        return redacted
    if isinstance(value, list):
        return [_redact_activation_payload(item) for item in value]
    return value


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
    serials: set[str] = set()
    while len(serials) < quantity:
        serials.add(generate_serial())
    return sorted(serials)


def hash_serial(serial: str) -> str:
    normalized = normalize_serial(serial)
    return hmac.new(
        SERIAL_HASH_SECRET,
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _windows_machine_guid() -> str:
    if os.name != "nt":
        return ""
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return str(value)
    except OSError:
        return ""


def get_machine_id() -> str:
    parts = [
        platform.node(),
        socket.gethostname(),
        getpass.getuser(),
        platform.platform(),
        str(Path.home()),
        os.environ.get("COMPUTERNAME", ""),
        os.environ.get("USERNAME", ""),
        os.environ.get("USERDOMAIN", ""),
        _windows_machine_guid(),
        MACHINE_ID_SALT,
    ]
    return "|".join(part for part in parts if part)


def get_machine_id_hash() -> str:
    return hashlib.sha256(get_machine_id().encode("utf-8")).hexdigest()


def _canonical_license_payload(payload: dict[str, Any]) -> bytes:
    data = dict(payload)
    data.pop("signature", None)
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sign_license_payload(payload: dict[str, Any]) -> str:
    return hmac.new(
        LICENSE_SIGNATURE_SECRET,
        _canonical_license_payload(payload),
        hashlib.sha256,
    ).hexdigest()


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_datetime(value: str) -> str:
    parsed = _parse_datetime(value)
    if not parsed:
        return value
    return parsed.astimezone().strftime("%d/%m/%Y %H:%M")


def _remaining_days(expires_at: str) -> int:
    expires = _parse_datetime(expires_at)
    if not expires:
        return 0
    seconds = (expires - datetime.now(timezone.utc)).total_seconds()
    return max(0, math.ceil(seconds / 86400))


def validate_license_payload(payload: dict[str, Any]) -> LicenseStatus:
    if not isinstance(payload, dict):
        return LicenseStatus(reason="invalid_payload")

    product = str(payload.get("product", ""))
    license_type = str(payload.get("license_type", ""))
    status = str(payload.get("status", ""))
    machine_id_hash = str(payload.get("machine_id_hash", ""))
    activated_at = str(payload.get("activated_at", ""))
    expires_at = str(payload.get("expires_at", ""))
    try:
        valid_days = int(payload.get("valid_days", VALID_DAYS) or VALID_DAYS)
    except (TypeError, ValueError):
        return LicenseStatus(reason="invalid_payload")
    signature = str(payload.get("signature", ""))

    if not signature or not hmac.compare_digest(signature, sign_license_payload(payload)):
        return LicenseStatus(reason="invalid_signature")
    if product != PRODUCT_NAME or license_type != LICENSE_TYPE or status != "activated":
        return LicenseStatus(reason="invalid_payload")
    if not hmac.compare_digest(machine_id_hash, get_machine_id_hash()):
        return LicenseStatus(
            product=product or PRODUCT_NAME,
            license_type=license_type or LICENSE_TYPE,
            activated_at=activated_at,
            expires_at=expires_at,
            valid_days=valid_days,
            reason="machine_mismatch",
        )

    expires = _parse_datetime(expires_at)
    if not expires:
        return LicenseStatus(reason="invalid_payload")
    days_remaining = _remaining_days(expires_at)
    if datetime.now(timezone.utc) > expires:
        return LicenseStatus(
            product=product,
            license_type=license_type,
            activated_at=activated_at,
            expires_at=expires_at,
            valid_days=valid_days,
            days_remaining=0,
            reason="expired",
        )

    return LicenseStatus(
        product=product,
        license_type=license_type,
        active=True,
        activated_at=activated_at,
        expires_at=expires_at,
        valid_days=valid_days,
        days_remaining=days_remaining,
        reason="active",
    )


class LicenseManager:
    def __init__(self, data_root: Path) -> None:
        self.data_root = Path(data_root)
        self.license_path = self.data_root / LICENSE_FILENAME

    def status(self) -> LicenseStatus:
        if not self.license_path.exists():
            return LicenseStatus(reason="no_license")
        try:
            payload = json.loads(self.license_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return LicenseStatus(reason="read_error")
        return validate_license_payload(payload)

    def is_activated(self) -> bool:
        return self.status().active

    def activate_online(self, serial: str) -> ActivationResult:
        normalized_serial = normalize_serial(serial)
        serial_is_valid = validate_serial(normalized_serial)
        machine_id_hash = get_machine_id_hash()
        logger.info(
            "Iniciando activación online. url=%s serial=%s machine_id_hash=%s validate_serial=%s",
            ACTIVATION_URL,
            _mask_serial(normalized_serial),
            _short_hash(machine_id_hash),
            serial_is_valid,
        )
        if not serial_is_valid:
            logger.warning(
                "Serial rechazado antes de enviar al servidor. serial=%s validate_serial=false",
                _mask_serial(normalized_serial),
            )
            return ActivationResult(False, "Clave de activación no válida.")

        request_payload = {
            "product": PRODUCT_NAME,
            "serial": normalized_serial,
            "machine_id_hash": machine_id_hash,
            "version": APP_VERSION,
        }
        logger.info(
            "Enviando petición de activación. payload=%s",
            _redact_activation_payload(request_payload),
        )
        request = urllib.request.Request(
            ACTIVATION_URL,
            data=json.dumps(request_payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": f"Manualtech/{APP_VERSION}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                http_status = getattr(response, "status", response.getcode())
                raw_response = response.read().decode("utf-8")
                logger.info("Respuesta HTTP de activación recibida. status=%s", http_status)
                response_payload = json.loads(raw_response)
                logger.info(
                    "Respuesta JSON de activación: %s",
                    _redact_activation_payload(response_payload),
                )
        except urllib.error.HTTPError as exc:
            logger.warning(
                "Error HTTP durante activación. status=%s reason=%s",
                exc.code,
                exc.reason,
                exc_info=True,
            )
            try:
                raw_response = exc.read().decode("utf-8")
                response_payload = json.loads(raw_response)
                logger.info(
                    "Respuesta JSON de error HTTP: %s",
                    _redact_activation_payload(response_payload),
                )
            except (OSError, json.JSONDecodeError) as error:
                logger.exception("No se pudo leer o parsear la respuesta HTTP de error: %s", error)
                return ActivationResult(
                    False,
                    "No se recibió una respuesta válida del servidor de activación.",
                )
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            logger.exception("Error de conexión durante activación: %s", error)
            return ActivationResult(
                False,
                "No se pudo conectar con el servidor de activación. "
                "La activación inicial requiere conexión a internet.",
            )
        except json.JSONDecodeError as error:
            logger.exception("La respuesta de activación no es JSON válido: %s", error)
            return ActivationResult(
                False,
                "No se recibió una respuesta válida del servidor de activación.",
            )

        if not response_payload.get("ok"):
            message = response_payload.get(
                "message",
                "No se pudo completar la activación. Inténtalo más tarde.",
            )
            logger.warning(
                "El servidor rechazó la activación. error=%s message=%s payload=%s",
                response_payload.get("error"),
                message,
                _redact_activation_payload(response_payload),
            )
            return ActivationResult(False, str(message))

        license_payload = response_payload.get("license")
        if not isinstance(license_payload, dict):
            logger.error(
                "La respuesta de activación no contiene un campo license válido. payload=%s",
                _redact_activation_payload(response_payload),
            )
            return ActivationResult(
                False,
                "La licencia recibida no es válida. Contacta con soporte.",
            )
        received_serial_hash = str(license_payload.get("serial_hash", ""))
        expected_serial_hash = hash_serial(normalized_serial)
        if not hmac.compare_digest(received_serial_hash, expected_serial_hash):
            logger.error(
                "El serial_hash recibido no coincide con el esperado. received=%s expected=%s",
                _short_hash(received_serial_hash),
                _short_hash(expected_serial_hash),
            )
            return ActivationResult(
                False,
                "La licencia recibida no es válida. Contacta con soporte.",
            )

        license_status = validate_license_payload(license_payload)
        logger.info(
            "Resultado de validate_license_payload. active=%s reason=%s expires_at=%s days_remaining=%s",
            license_status.active,
            license_status.reason,
            license_status.expires_at,
            license_status.days_remaining,
        )
        if not license_status.active:
            logger.warning(
                "Licencia recibida no activa. reason=%s blocking_message=%s",
                license_status.reason,
                license_status.blocking_message,
            )
            if license_status.reason == "invalid_signature":
                return ActivationResult(False, "La firma de la licencia no es válida.")
            if license_status.blocking_message:
                return ActivationResult(False, license_status.blocking_message)
            return ActivationResult(
                False,
                "La licencia recibida no es válida. Contacta con soporte.",
            )

        try:
            self.data_root.mkdir(parents=True, exist_ok=True)
            logger.info("Guardando licencia local en: %s", self.license_path)
            self.license_path.write_text(
                json.dumps(license_payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info("Licencia local guardada correctamente.")
        except OSError as error:
            logger.exception(
                "No se pudo guardar license.json en %s: %s",
                self.license_path,
                error,
            )
            return ActivationResult(False, "No se pudo guardar la activación.")

        logger.info(
            "Activación completada correctamente. serial=%s machine_id_hash=%s",
            _mask_serial(normalized_serial),
            _short_hash(machine_id_hash),
        )
        return ActivationResult(
            True,
            response_payload.get("message", "Manualtech Beta activado correctamente."),
        )


class ActivationDialog(QDialog):
    def __init__(self, license_manager: LicenseManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.license_manager = license_manager
        self.setWindowTitle("Activación Beta de Manualtech")
        self.setMinimumWidth(520)
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

        title = QLabel("<b>Manualtech Beta</b><br>Introduce tu clave de activación Beta")
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setWordWrap(True)
        header.addWidget(title, 1)
        layout.addLayout(header)

        description = QLabel(
            "Introduce tu clave de activación Beta. La activación requiere "
            "conexión a internet solo la primera vez. Después podrás usar "
            "Manualtech offline hasta que finalice el periodo Beta."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

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

        self.activate_button.setEnabled(False)
        self.activate_button.setText("Activando...")
        try:
            result = self.license_manager.activate_online(serial)
        finally:
            self.activate_button.setEnabled(True)
            self.activate_button.setText("Activar")

        if not result.ok:
            QMessageBox.warning(self, "Activación", result.message)
            return

        QMessageBox.information(self, "Activación", result.message)
        self.accept()


def cli_main() -> int:
    parser = argparse.ArgumentParser(description="Genera seriales Beta válidos de Manualtech.")
    parser.add_argument(
        "--cantidad",
        type=int,
        default=1,
        help="Número de seriales a generar.",
    )
    parser.add_argument(
        "--salida",
        type=Path,
        default=None,
        help="Archivo .txt donde guardar los seriales generados.",
    )
    args = parser.parse_args()
    serials = generate_serials(args.cantidad)
    if args.salida:
        args.salida.write_text("\n".join(serials) + "\n", encoding="utf-8")
        print(f"Seriales generados: {len(serials)}")
        print(f"Archivo: {args.salida}")
    else:
        for serial in serials:
            print(serial)
    return 0
