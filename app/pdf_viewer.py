from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

import fitz
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


logger = logging.getLogger(__name__)


class PDFViewerService:
    def __init__(self, previews_dir: Path, max_cached_previews: int = 800) -> None:
        self.previews_dir = Path(previews_dir)
        self.max_cached_previews = max_cached_previews
        self.previews_dir.mkdir(parents=True, exist_ok=True)

    def get_preview_path(
        self,
        stored_path: str | Path,
        manual_id: int,
        page_number: int,
        zoom: float = 1.8,
        force: bool = False,
    ) -> Path:
        pdf_path = Path(stored_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"No se encontró el PDF: {pdf_path}")
        if page_number < 1:
            raise ValueError("El número de página debe ser 1 o superior.")

        preview_path = self.previews_dir / f"manual_{manual_id}_page_{page_number}.png"
        if preview_path.exists() and not force:
            return preview_path

        document = fitz.open(pdf_path)
        try:
            if page_number > document.page_count:
                raise ValueError(
                    f"El PDF solo tiene {document.page_count} páginas."
                )
            page = document.load_page(page_number - 1)
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            pixmap.save(str(preview_path))
        finally:
            document.close()

        logger.info("Preview renderizada: %s", preview_path)
        self._enforce_cache_limit()
        return preview_path

    def open_pdf(self, stored_path: str | Path, page_number: int | None = None) -> bool:
        pdf_path = Path(stored_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"No se encontró el PDF: {pdf_path}")

        if page_number is not None and page_number < 1:
            page_number = 1

        if os.name == "nt":
            if page_number and self._open_pdf_on_windows_page(pdf_path, page_number):
                return True
            os.startfile(str(pdf_path))  # type: ignore[attr-defined]
            return True

        url = self._pdf_page_url(pdf_path, page_number)
        return QDesktopServices.openUrl(url)

    def _open_pdf_on_windows_page(self, pdf_path: Path, page_number: int) -> bool:
        for command in self._windows_page_commands(pdf_path, page_number):
            try:
                subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                )
                logger.info(
                    "PDF abierto en página %s con: %s",
                    page_number,
                    command[0],
                )
                return True
            except OSError:
                continue
            except Exception:
                logger.exception("No se pudo abrir PDF con comando: %s", command)

        return QDesktopServices.openUrl(self._pdf_page_url(pdf_path, page_number))

    def _windows_page_commands(self, pdf_path: Path, page_number: int) -> list[list[str]]:
        commands: list[list[str]] = []

        for sumatra in self._find_executables(
            "SumatraPDF.exe",
            [
                r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
                r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
            ],
        ):
            commands.append([sumatra, "-page", str(page_number), str(pdf_path)])

        for adobe in self._find_executables(
            "AcroRd32.exe",
            [
                r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
                r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
                r"C:\Program Files\Adobe\Acrobat Reader\Reader\AcroRd32.exe",
                r"C:\Program Files (x86)\Adobe\Acrobat Reader\Reader\AcroRd32.exe",
            ],
        ):
            commands.append([adobe, "/A", f"page={page_number}", str(pdf_path)])

        for acrobat in self._find_executables(
            "Acrobat.exe",
            [
                r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
                r"C:\Program Files\Adobe\Acrobat\Acrobat\Acrobat.exe",
            ],
        ):
            commands.append([acrobat, "/A", f"page={page_number}", str(pdf_path)])

        page_url = self._pdf_page_url(pdf_path, page_number).toString()
        for browser in self._find_executables(
            "msedge.exe",
            [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ],
        ):
            commands.append([browser, "--new-window", page_url])

        for browser in self._find_executables(
            "chrome.exe",
            [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ],
        ):
            commands.append([browser, "--new-window", page_url])

        for browser in self._find_executables(
            "firefox.exe",
            [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            ],
        ):
            commands.append([browser, "-new-window", page_url])

        return commands

    @staticmethod
    def _find_executables(executable_name: str, known_paths: list[str]) -> list[str]:
        found: list[str] = []
        path_match = shutil.which(executable_name)
        if path_match:
            found.append(path_match)

        for known_path in known_paths:
            path = Path(known_path)
            if path.exists():
                path_text = str(path)
                if path_text not in found:
                    found.append(path_text)
        return found

    @staticmethod
    def _pdf_page_url(pdf_path: Path, page_number: int | None) -> QUrl:
        url = QUrl.fromLocalFile(str(pdf_path))
        if page_number:
            url.setFragment(f"page={page_number}")
        return url

    def clear_previews_for_manual(self, manual_id: int) -> None:
        for preview in self.previews_dir.glob(f"manual_{manual_id}_page_*.png"):
            try:
                preview.unlink(missing_ok=True)
            except OSError:
                logger.exception("No se pudo eliminar preview: %s", preview)

    def _enforce_cache_limit(self) -> None:
        if self.max_cached_previews <= 0:
            return

        previews = list(self.previews_dir.glob("manual_*_page_*.png"))
        overflow = len(previews) - self.max_cached_previews
        if overflow <= 0:
            return

        previews.sort(key=lambda path: path.stat().st_mtime)
        for preview in previews[:overflow]:
            try:
                preview.unlink(missing_ok=True)
            except OSError:
                logger.exception("No se pudo limpiar preview antigua: %s", preview)
