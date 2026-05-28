from __future__ import annotations

import argparse
from pathlib import Path

from database import init_db, seed_serials


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Carga seriales Beta de Manualtech en la base de activación."
    )
    parser.add_argument("archivo", type=Path, help="Archivo .txt con un serial por línea.")
    args = parser.parse_args()

    if not args.archivo.exists():
        raise SystemExit(f"No existe el archivo: {args.archivo}")

    serials = [
        line.strip()
        for line in args.archivo.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    init_db()
    inserted, skipped = seed_serials(serials)
    print(f"Seriales leídos: {len(serials)}")
    print(f"Seriales cargados: {inserted}")
    print(f"Seriales omitidos: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
