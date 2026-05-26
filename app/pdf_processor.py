from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Callable, Iterator

import fitz

from .models import PageText
from .paths import resource_path


logger = logging.getLogger(__name__)
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
SUPPORTED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
}


class PDFProcessingError(RuntimeError):
    """Error controlado al leer, copiar o extraer un PDF."""


class PDFProcessor:
    def calculate_sha256(self, pdf_path: Path) -> str:
        path = Path(pdf_path)
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def calculate_image_folder_hash(self, image_paths: list[Path]) -> str:
        digest = hashlib.sha256()
        digest.update(b"manualtech-image-folder-v1")
        for image_path in image_paths:
            path = Path(image_path)
            digest.update(path.name.encode("utf-8", errors="ignore"))
            with path.open("rb") as file:
                for chunk in iter(lambda: file.read(1024 * 1024), b""):
                    digest.update(chunk)
        return f"images:{digest.hexdigest()}"

    def copy_pdf_to_library(self, source_path: Path, manuals_dir: Path) -> Path:
        source = Path(source_path)
        if source.suffix.lower() != ".pdf":
            raise PDFProcessingError("El archivo seleccionado no es un PDF.")
        if not source.exists():
            raise PDFProcessingError("El archivo PDF seleccionado no existe.")

        manuals_dir = Path(manuals_dir)
        manuals_dir.mkdir(parents=True, exist_ok=True)
        destination = self.unique_destination(source.name, manuals_dir)
        shutil.copy2(source, destination)
        logger.info("PDF copiado a biblioteca: %s", destination)
        return destination

    def list_image_files(self, folder_path: Path) -> list[Path]:
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            raise PDFProcessingError("La carpeta de imágenes seleccionada no existe.")

        images = [
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        ]
        images.sort(key=lambda path: self._natural_sort_key(path.name))
        return images

    def create_pdf_from_images(
        self,
        image_paths: list[Path],
        output_path: Path,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        if not image_paths:
            raise PDFProcessingError(
                "La carpeta no contiene imágenes compatibles: JPG, PNG, BMP, TIFF o WEBP."
            )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        document = fitz.open()

        try:
            for index, image_path in enumerate(image_paths, start=1):
                try:
                    pixmap = fitz.Pixmap(str(image_path))
                    if pixmap.alpha:
                        pixmap = fitz.Pixmap(fitz.csRGB, pixmap)
                    rect = fitz.Rect(0, 0, pixmap.width, pixmap.height)
                    page = document.new_page(width=pixmap.width, height=pixmap.height)
                    page.insert_image(rect, pixmap=pixmap)
                except Exception as exc:
                    raise PDFProcessingError(
                        f"No se pudo convertir la imagen '{image_path.name}' a PDF: {exc}"
                    ) from exc
                finally:
                    if progress_callback:
                        progress_callback(index, len(image_paths))

            document.save(output, garbage=4, deflate=True)
        finally:
            document.close()

        logger.info("PDF creado desde carpeta de imágenes: %s", output)
        return output

    def extract_pages(
        self,
        pdf_path: Path,
        use_ocr: bool = False,
        ocr_language: str = "auto",
        ocr_dpi: int = 150,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[PageText]:
        return list(
            self.iter_pages(
                pdf_path,
                use_ocr=use_ocr,
                ocr_language=ocr_language,
                ocr_dpi=ocr_dpi,
                progress_callback=progress_callback,
            )
        )

    def iter_pages(
        self,
        pdf_path: Path,
        use_ocr: bool = False,
        ocr_language: str = "auto",
        ocr_dpi: int = 150,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Iterator[PageText]:
        path = Path(pdf_path)
        if not path.exists():
            raise PDFProcessingError("No se encontró el PDF para extraer texto.")

        try:
            document = fitz.open(path)
        except Exception as exc:
            raise PDFProcessingError(f"No se pudo abrir el PDF: {exc}") from exc

        try:
            if document.is_encrypted and document.needs_pass:
                raise PDFProcessingError(
                    "El PDF está protegido con contraseña y no se puede indexar."
                )

            tessdata = self.find_tessdata() if use_ocr else None
            ocr_available = bool(tessdata)
            resolved_language = self.resolve_ocr_language(tessdata, ocr_language)
            if use_ocr and not ocr_available:
                logger.warning(
                    "OCR solicitado, pero Tesseract no está disponible en el sistema."
                )

            for index in range(document.page_count):
                text = ""
                try:
                    page = document.load_page(index)
                    text = page.get_text("text") or ""
                    if use_ocr and not text.strip() and ocr_available:
                        text = self._extract_text_with_ocr(
                            page,
                            language=resolved_language,
                            dpi=ocr_dpi,
                            tessdata=tessdata,
                        )
                except Exception:
                    logger.exception("No se pudo extraer texto de la página %s", index + 1)
                yield PageText(page_number=index + 1, text=self._clean_text(text))
                if progress_callback:
                    progress_callback(index + 1, document.page_count)
        finally:
            document.close()

    @classmethod
    def find_tessdata(cls) -> str | None:
        app_dir = (
            Path(sys.executable).resolve().parent
            if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parent.parent
        )
        candidates = [
            resource_path("data", "tessdata"),
            app_dir / "data" / "tessdata",
            Path.cwd() / "data" / "tessdata",
            os.environ.get("TESSDATA_PREFIX"),
            r"C:\Program Files\Tesseract-OCR\tessdata",
            r"C:\Program Files (x86)\Tesseract-OCR\tessdata",
        ]
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                traineddata_files = list(Path(candidate).glob("*.traineddata"))
                if traineddata_files:
                    return str(Path(candidate))
        try:
            return str(fitz.get_tessdata(None))
        except Exception:
            return None

    @classmethod
    def is_ocr_available(cls) -> bool:
        return cls.find_tessdata() is not None

    @staticmethod
    def resolve_ocr_language(tessdata: str | None, requested: str) -> str:
        requested = (requested or "auto").strip()
        if requested != "auto":
            return requested
        if not tessdata:
            return "eng"

        tessdata_path = Path(tessdata)
        has_spanish = (tessdata_path / "spa.traineddata").exists()
        has_english = (tessdata_path / "eng.traineddata").exists()
        if has_spanish and has_english:
            return "spa+eng"
        if has_spanish:
            return "spa"
        return "eng"

    def ocr_status_message(self) -> str:
        tessdata = self.find_tessdata()
        if tessdata:
            return f"OCR local disponible: {tessdata}"
        return (
            "OCR local no disponible. Instala Tesseract OCR para indexar PDFs "
            "escaneados o formados solo por imágenes."
        )

    def _extract_text_with_ocr(
        self,
        page: fitz.Page,
        language: str,
        dpi: int,
        tessdata: str | None,
    ) -> str:
        try:
            text_page = page.get_textpage_ocr(
                language=language,
                dpi=dpi,
                full=True,
                tessdata=tessdata,
            )
            return text_page.extractText() or ""
        except Exception as exc:
            logger.warning(
                "OCR con idioma '%s' falló en página %s: %s",
                language,
                page.number + 1,
                exc,
            )
            if language != "eng":
                text_page = page.get_textpage_ocr(
                    language="eng",
                    dpi=dpi,
                    full=True,
                    tessdata=tessdata,
                )
                return text_page.extractText() or ""
            raise

    def unique_destination(self, filename: str, manuals_dir: Path) -> Path:
        safe_name = self._safe_filename(filename)
        destination = manuals_dir / safe_name
        if not destination.exists():
            return destination

        stem = destination.stem
        suffix = destination.suffix or ".pdf"
        counter = 2
        while True:
            candidate = manuals_dir / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    @staticmethod
    def _natural_sort_key(value: str) -> list[int | str]:
        return [
            int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", value)
        ]

    @staticmethod
    def _safe_filename(filename: str) -> str:
        cleaned = INVALID_FILENAME_CHARS.sub("_", filename).strip(" .")
        if not cleaned:
            cleaned = "manual.pdf"
        if not cleaned.lower().endswith(".pdf"):
            cleaned = f"{cleaned}.pdf"
        return cleaned

    @staticmethod
    def _clean_text(text: str) -> str:
        return (
            text.replace("\x00", "")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .strip()
        )
