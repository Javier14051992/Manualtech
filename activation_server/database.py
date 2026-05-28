from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PRODUCT_NAME = "Manualtech"
LICENSE_TYPE = "Beta 30 días"
VALID_DAYS = 30
DB_PATH = Path(os.environ.get("MANUALTECH_ACTIVATION_DB", "activation_server.sqlite"))

SERIAL_PREFIX = "MT"
SERIAL_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
SERIAL_SECRET = os.environ.get(
    "MANUALTECH_SERIAL_SECRET",
    "Manualtech-MSL-Beta-2026-local-activation",
).encode("utf-8")
SERIAL_HASH_SECRET = os.environ.get(
    "MANUALTECH_SERIAL_HASH_SECRET",
    "Manualtech-MSL-Beta-2026-serial-hash",
).encode("utf-8")

# Para la beta se usa HMAC compartido con la app. Para producción final conviene
# usar firma asimétrica: servidor con clave privada y app con clave pública.
LICENSE_SIGNATURE_SECRET = os.environ.get(
    "MANUALTECH_LICENSE_SECRET",
    "Manualtech-MSL-Beta-2026-license-signature",
).encode("utf-8")

SERIAL_BODY_LENGTH = 12
SERIAL_CHECKSUM_LENGTH = 4


def connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS serials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_hash TEXT NOT NULL UNIQUE,
                product TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'available',
                machine_id_hash TEXT,
                activated_at TEXT,
                expires_at TEXT,
                used_at TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_serials_status ON serials(status)"
        )


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
    digest = hmac.new(SERIAL_SECRET, payload.encode("ascii"), hashlib.sha256).digest()
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


def hash_serial(serial: str) -> str:
    normalized = normalize_serial(serial)
    return hmac.new(
        SERIAL_HASH_SECRET,
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


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


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def seed_serials(serials: list[str]) -> tuple[int, int]:
    init_db()
    inserted = 0
    skipped = 0
    now = iso(utc_now())
    with connection() as conn:
        for serial in serials:
            normalized = normalize_serial(serial)
            if not validate_serial(normalized):
                skipped += 1
                continue
            try:
                conn.execute(
                    """
                    INSERT INTO serials (serial_hash, product, status, created_at)
                    VALUES (?, ?, 'available', ?)
                    """,
                    (hash_serial(normalized), PRODUCT_NAME, now),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1
    return inserted, skipped


def activate_serial(
    *,
    product: str,
    serial: str,
    machine_id_hash: str,
) -> dict[str, Any]:
    init_db()
    normalized = normalize_serial(serial)
    if product != PRODUCT_NAME or not validate_serial(normalized):
        return {
            "ok": False,
            "error": "invalid_serial",
            "message": "Clave de activación no válida.",
        }
    if not machine_id_hash or len(machine_id_hash) < 32:
        return {
            "ok": False,
            "error": "invalid_machine",
            "message": "No se pudo identificar el equipo para la activación.",
        }

    serial_hash = hash_serial(normalized)
    now = utc_now()
    expires = now + timedelta(days=VALID_DAYS)

    conn = connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """
            SELECT id, status
            FROM serials
            WHERE serial_hash = ? AND product = ?
            """,
            (serial_hash, PRODUCT_NAME),
        ).fetchone()
        if not row:
            conn.rollback()
            return {
                "ok": False,
                "error": "invalid_serial",
                "message": "Clave de activación no válida.",
            }
        if row["status"] != "available":
            conn.rollback()
            return {
                "ok": False,
                "error": "serial_already_used",
                "message": "Esta clave de activación ya ha sido utilizada.",
            }

        activated_at = iso(now)
        expires_at = iso(expires)
        license_payload = {
            "product": PRODUCT_NAME,
            "license_type": LICENSE_TYPE,
            "status": "activated",
            "serial_hash": serial_hash,
            "machine_id_hash": machine_id_hash,
            "activated_at": activated_at,
            "expires_at": expires_at,
            "valid_days": VALID_DAYS,
        }
        license_payload["signature"] = sign_license_payload(license_payload)

        conn.execute(
            """
            UPDATE serials
            SET status = 'used',
                machine_id_hash = ?,
                activated_at = ?,
                expires_at = ?,
                used_at = ?
            WHERE id = ?
            """,
            (machine_id_hash, activated_at, expires_at, activated_at, row["id"]),
        )
        conn.commit()
        return {
            "ok": True,
            "license": license_payload,
            "message": "Manualtech Beta activado correctamente.",
        }
    except sqlite3.Error:
        conn.rollback()
        return {
            "ok": False,
            "error": "server_error",
            "message": "No se pudo completar la activación. Inténtalo más tarde.",
        }
    finally:
        conn.close()
