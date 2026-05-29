from __future__ import annotations

import logging
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.licensing import ACTIVATION_URL, LicenseManager  # noqa: E402
from app.paths import user_root  # noqa: E402


def setup_logging(data_root: Path) -> Path:
    logs_dir = data_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "app.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8",
    )
    return log_path


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python scripts/test_activation_from_manualtech.py MT-XXXX-XXXX-XXXX-XXXX")
        return 2

    serial = sys.argv[1]
    data_root = user_root()
    log_path = setup_logging(data_root)
    manager = LicenseManager(data_root)

    print(f"Activation URL: {ACTIVATION_URL}")
    print(f"Data root: {data_root}")
    print(f"License path: {manager.license_path}")
    print(f"Log path: {log_path}")
    print("Activando...")

    result = manager.activate_online(serial)
    print(f"Resultado OK: {result.ok}")
    print(f"Mensaje: {result.message}")

    status = manager.status()
    print("Estado final:")
    print(f"  Producto: {status.product}")
    print(f"  Estado: {status.state_label}")
    print(f"  Tipo: {status.license_type}")
    print(f"  Razón interna: {status.reason}")
    print(f"  Fecha de activación: {status.activated_at_label}")
    print(f"  Fecha de caducidad: {status.expires_at_label}")
    print(f"  Días restantes: {status.days_remaining}")
    print(f"  license.json creado: {manager.license_path.exists()}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
