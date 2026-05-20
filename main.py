from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app.database import Database
from app.paths import APP_NAME, app_root, resource_path, user_root
from app.pdf_viewer import PDFViewerService
from app.search_engine import SearchEngine
from app.ui_main import MainWindow


def setup_logging(data_root: Path) -> None:
    logs_dir = data_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=logs_dir / "app.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8",
    )


def main() -> int:
    application_root = app_root()
    data_root = user_root()
    setup_logging(data_root)
    logging.info("Iniciando %s", APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("ManualTechLocal")
    app.setStyle("Fusion")

    logo_path = resource_path("assets", "manualtech_logo.png")
    if logo_path.exists():
        app.setWindowIcon(QIcon(str(logo_path)))

    try:
        database = Database(data_root)
        search_engine = SearchEngine(database)
        pdf_viewer = PDFViewerService(database.previews_dir)

        window = MainWindow(
            base_dir=application_root,
            database=database,
            search_engine=search_engine,
            pdf_viewer=pdf_viewer,
        )
        window.show()
        return app.exec()
    except Exception as exc:  # pragma: no cover - ultimo salvavidas de arranque
        logging.exception("No se pudo iniciar la aplicacion")
        QMessageBox.critical(
            None,
            APP_NAME,
            f"No se pudo iniciar la aplicacion:\n{exc}",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
