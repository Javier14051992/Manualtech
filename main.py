from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from app.database import Database
from app.licensing import ActivationDialog, LicenseManager
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
    app.setOrganizationName("MSL MotorSuiteLab")
    app.setStyle("Fusion")

    logo_path = resource_path("assets", "manualtech_logo.png")
    if logo_path.exists():
        app.setWindowIcon(QIcon(str(logo_path)))

    try:
        license_manager = LicenseManager(data_root)
        if not license_manager.is_activated():
            activation_dialog = ActivationDialog(license_manager)
            if activation_dialog.exec() != QDialog.DialogCode.Accepted:
                return 0

        database = Database(data_root)
        search_engine = SearchEngine(database)
        pdf_viewer = PDFViewerService(database.previews_dir)

        window = MainWindow(
            base_dir=application_root,
            database=database,
            search_engine=search_engine,
            pdf_viewer=pdf_viewer,
            license_status=license_manager.status(),
        )
        window.show()
        return app.exec()
    except Exception as exc:  # pragma: no cover - ultimo salvavidas de arranque
        logging.exception("No se pudo iniciar la aplicación")
        QMessageBox.critical(
            None,
            APP_NAME,
            f"No se pudo iniciar la aplicación:\n{exc}",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
