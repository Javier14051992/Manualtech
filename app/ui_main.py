from __future__ import annotations

import html
import logging
import sqlite3
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .database import Database
from .licensing import LicenseStatus
from .models import Manual, ManualMetadata, SearchResult
from .paths import resource_path
from .pdf_processor import PDFProcessingError, PDFProcessor
from .pdf_viewer import PDFViewerService
from .search_engine import SearchEngine


logger = logging.getLogger(__name__)


class MetadataDialog(QDialog):
    CATEGORIES = [
        "Coche",
        "Moto",
        "Reparación general",
        "Electrónica / cuadros / diagnosis",
        "Herramientas / procedimientos",
        "Ficha propia",
        "Otro",
    ]

    def __init__(
        self,
        source_path: Path,
        parent: QWidget | None = None,
        default_category: str = "Coche",
        source_type: str = "pdf",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Datos del manual")
        self.setMinimumWidth(520)
        self.source_type = source_type

        layout = QVBoxLayout(self)
        intro = QLabel("Completa los datos disponibles para clasificar el manual.")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.CATEGORIES)
        category_index = self.category_combo.findText(default_category)
        if category_index >= 0:
            self.category_combo.setCurrentIndex(category_index)
        self.category_combo.currentTextChanged.connect(self._update_category_fields)

        self.title_edit = QLineEdit(source_path.stem)
        self.topic_edit = QLineEdit()
        self.brand_edit = QLineEdit()
        self.model_edit = QLineEdit()
        self.year_edit = QLineEdit()
        self.engine_edit = QLineEdit()
        self.system_edit = QLineEdit()
        self.document_type_edit = QLineEdit()
        self.language_edit = QLineEdit("es")
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(90)

        self.topic_edit.setPlaceholderText("Ej. Cuadros digitales, ABS, diagnosis")
        self.year_edit.setPlaceholderText("Ej. 2008 o 2008-2012")
        self.system_edit.setPlaceholderText("Ej. Frenos, motor, electricidad")
        self.document_type_edit.setPlaceholderText("Ej. Manual de taller")

        form.addRow("Categoría:", self.category_combo)
        form.addRow("Título:", self.title_edit)
        form.addRow("Tema:", self.topic_edit)
        form.addRow("Marca:", self.brand_edit)
        form.addRow("Modelo:", self.model_edit)
        form.addRow("Año:", self.year_edit)
        form.addRow("Motor:", self.engine_edit)
        form.addRow("Sistema:", self.system_edit)
        form.addRow("Tipo de documento:", self.document_type_edit)
        form.addRow("Idioma:", self.language_edit)
        form.addRow("Notas:", self.notes_edit)
        layout.addLayout(form)
        self._update_category_fields(self.category_combo.currentText())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Añadir")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def metadata(self) -> ManualMetadata:
        return ManualMetadata(
            title=self.title_edit.text().strip(),
            document_category=self.category_combo.currentText().strip(),
            topic=self.topic_edit.text().strip(),
            brand=self.brand_edit.text().strip(),
            model=self.model_edit.text().strip(),
            year=self.year_edit.text().strip(),
            engine=self.engine_edit.text().strip(),
            system=self.system_edit.text().strip(),
            document_type=self.document_type_edit.text().strip(),
            language=self.language_edit.text().strip(),
            notes=self.notes_edit.toPlainText().strip(),
            source_type=self.source_type,
        )

    def _update_category_fields(self, category: str) -> None:
        if category == "Moto":
            self.topic_edit.setPlaceholderText("Ej. Motor, chasis, electricidad")
            self.brand_edit.setPlaceholderText("Ej. Yamaha, Honda, BMW")
            self.model_edit.setPlaceholderText("Ej. MT-07, CBR600RR")
            self.engine_edit.setPlaceholderText("Ej. 689 cc")
            self.system_edit.setPlaceholderText("Ej. Frenos, motor, transmisión")
        elif category == "Coche":
            self.topic_edit.setPlaceholderText("Ej. Manual completo, motor, electricidad")
            self.brand_edit.setPlaceholderText("Ej. Audi, Ford, Toyota")
            self.model_edit.setPlaceholderText("Ej. A3, Focus, Corolla")
            self.engine_edit.setPlaceholderText("Ej. 1.9 TDI, 2.0 HDI")
            self.system_edit.setPlaceholderText("Ej. Frenos, motor, electricidad")
        else:
            self.topic_edit.setPlaceholderText("Ej. Cuadros digitales, diagnosis, ECU")
            self.brand_edit.setPlaceholderText("Opcional si aplica")
            self.model_edit.setPlaceholderText("Opcional si aplica")
            self.engine_edit.setPlaceholderText("Opcional si aplica")
            self.system_edit.setPlaceholderText("Ej. Cuadros, airbag, ABS, inyección")


class SearchResultCard(QFrame):
    selected = Signal(object)
    view_requested = Signal(object)
    open_requested = Signal(object)

    def __init__(self, result: SearchResult, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.result = result
        self.setObjectName("resultCard")
        self.setProperty("selected", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel(
            f"<b>{html.escape(result.display_title)}</b> "
            f"<span style='color:#667085;'>Página {result.page_number}</span>"
        )
        title.setTextFormat(Qt.TextFormat.RichText)
        title.setWordWrap(True)
        layout.addWidget(title)

        metadata = result.metadata_summary or "Sin metadatos"
        metadata_label = QLabel(html.escape(metadata))
        metadata_label.setObjectName("resultMeta")
        metadata_label.setWordWrap(True)
        layout.addWidget(metadata_label)

        snippet = QLabel(self._snippet_to_html(result.snippet))
        snippet.setObjectName("resultSnippet")
        snippet.setTextFormat(Qt.TextFormat.RichText)
        snippet.setWordWrap(True)
        layout.addWidget(snippet)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.view_button = QPushButton("Ver página")
        self.open_button = QPushButton("Abrir PDF")
        self.view_button.setObjectName("secondaryButton")
        self.open_button.setObjectName("secondaryButton")
        self.view_button.clicked.connect(lambda: self.view_requested.emit(self.result))
        self.open_button.clicked.connect(lambda: self.open_requested.emit(self.result))
        button_row.addWidget(self.view_button)
        button_row.addWidget(self.open_button)
        layout.addLayout(button_row)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.result)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    @staticmethod
    def _snippet_to_html(snippet: str) -> str:
        if not snippet.strip():
            return "<span style='color:#667085;'>Sin fragmento disponible.</span>"
        escaped = html.escape(snippet)
        escaped = escaped.replace(
            "[[H]]",
            "<span style='background:#fff1a8;color:#111827;font-weight:700;'>",
        )
        escaped = escaped.replace("[[/H]]", "</span>")
        return escaped.replace("\n", "<br>")


class LibraryDialog(QDialog):
    def __init__(
        self,
        database: Database,
        pdf_viewer: PDFViewerService,
        reindex_callback: Callable[[], None],
        changed_callback: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.database = database
        self.pdf_viewer = pdf_viewer
        self.reindex_callback = reindex_callback
        self.changed_callback = changed_callback

        self.setWindowTitle("Gestionar biblioteca")
        self.setMinimumSize(620, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QLabel("Biblioteca local")
        header.setObjectName("panelTitle")
        self.library_count = QLabel("0 manuales")
        self.library_count.setObjectName("mutedText")

        self.manual_list = QListWidget()
        self.manual_list.setObjectName("manualList")
        self.manual_list.itemDoubleClicked.connect(self._open_selected_manual)

        button_row = QHBoxLayout()
        self.open_button = QPushButton("Abrir PDF")
        self.reindex_button = QPushButton("Reindexar todo")
        self.delete_button = QPushButton("Eliminar manual")
        self.close_button = QPushButton("Cerrar")
        self.open_button.setObjectName("secondaryButton")
        self.reindex_button.setObjectName("secondaryButton")
        self.delete_button.setObjectName("dangerButton")

        self.open_button.clicked.connect(self._open_selected_manual)
        self.reindex_button.clicked.connect(self._reindex_all)
        self.delete_button.clicked.connect(self._delete_selected_manual)
        self.close_button.clicked.connect(self.accept)

        button_row.addWidget(self.open_button)
        button_row.addWidget(self.reindex_button)
        button_row.addWidget(self.delete_button)
        button_row.addStretch(1)
        button_row.addWidget(self.close_button)

        layout.addWidget(header)
        layout.addWidget(self.library_count)
        layout.addWidget(self.manual_list, 1)
        layout.addLayout(button_row)

        self.reload()

    def reload(self) -> None:
        self.manual_list.clear()
        manuals = self.database.list_manuals()
        for manual in manuals:
            item = QListWidgetItem(self._manual_item_text(manual))
            item.setData(Qt.ItemDataRole.UserRole, manual.id)
            item.setToolTip(str(Path(manual.stored_path)))
            self.manual_list.addItem(item)

        suffix = "manual" if len(manuals) == 1 else "manuales"
        self.library_count.setText(f"{len(manuals)} {suffix}")

    def _current_manual(self) -> Manual | None:
        item = self.manual_list.currentItem()
        if item is None:
            QMessageBox.information(
                self,
                "Sin selección",
                "Selecciona un manual primero.",
            )
            return None
        return self.database.get_manual(int(item.data(Qt.ItemDataRole.UserRole)))

    def _open_selected_manual(self) -> None:
        manual = self._current_manual()
        if manual is None:
            return
        try:
            self.pdf_viewer.open_pdf(manual.stored_path)
        except Exception as exc:
            QMessageBox.critical(self, "No se pudo abrir el PDF", str(exc))

    def _delete_selected_manual(self) -> None:
        manual = self._current_manual()
        if manual is None:
            return

        reply = QMessageBox.question(
            self,
            "Eliminar manual",
            f"¿Eliminar de la biblioteca local?\n\n{manual.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        deleted = self.database.delete_manual(manual.id)
        if deleted:
            try:
                Path(deleted.stored_path).unlink(missing_ok=True)
            except OSError:
                logger.exception("No se pudo eliminar el PDF almacenado")
            self.pdf_viewer.clear_previews_for_manual(manual.id)

        self.reload()
        self.changed_callback()

    def _reindex_all(self) -> None:
        self.reindex_callback()
        self.reload()
        self.changed_callback()

    @staticmethod
    def _manual_item_text(manual: Manual) -> str:
        details = manual.metadata_summary or "Sin metadatos"
        return f"{manual.display_title}\n{details}"


class MainWindow(QMainWindow):
    def __init__(
        self,
        base_dir: Path,
        database: Database,
        search_engine: SearchEngine,
        pdf_viewer: PDFViewerService,
        license_status: LicenseStatus | None = None,
    ) -> None:
        super().__init__()
        self.base_dir = Path(base_dir)
        self.database = database
        self.search_engine = search_engine
        self.pdf_viewer = pdf_viewer
        self.license_status = license_status or LicenseStatus(active=True)
        self.pdf_processor = PDFProcessor()
        self.result_cards: list[SearchResultCard] = []

        self.logo_path = resource_path("assets", "manualtech_logo.png")

        self.setWindowTitle("Manualtech")
        if self.logo_path.exists():
            self.setWindowIcon(QIcon(str(self.logo_path)))
        self.resize(1320, 820)
        self.setMinimumSize(1100, 680)

        self._build_ui()
        self._apply_styles()
        self._load_manuals()
        self.statusBar().showMessage("Listo")

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        top_panel = QWidget()
        top_panel.setObjectName("topPanel")
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(18, 14, 18, 14)
        top_layout.setSpacing(12)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(12)

        if self.logo_path.exists():
            logo = QLabel()
            logo.setObjectName("brandLogo")
            logo_pixmap = QPixmap(str(self.logo_path))
            logo.setPixmap(
                logo_pixmap.scaled(
                    62,
                    62,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            logo.setFixedSize(66, 66)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            brand_row.addWidget(logo)

        title_stack = QVBoxLayout()
        title_stack.setSpacing(2)
        title = QLabel("Manualtech")
        title.setObjectName("appTitle")
        subtitle = QLabel("Buscador local de manuales de taller")
        subtitle.setObjectName("appSubtitle")
        title_stack.addWidget(title)
        title_stack.addWidget(subtitle)
        brand_row.addLayout(title_stack)
        brand_row.addStretch(1)
        top_layout.addLayout(brand_row)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Buscar averías, procedimientos, piezas, códigos o sistemas..."
        )
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.returnPressed.connect(self._run_search)

        self.search_button = QPushButton("Buscar")
        self.add_pdf_button = QPushButton("Añadir PDF")
        self.add_folder_button = QPushButton("Añadir carpeta")
        self.library_button = QPushButton("Gestionar biblioteca")
        self.license_button = QPushButton("Estado de licencia")
        self.ocr_checkbox = QCheckBox("OCR local")
        self.ocr_checkbox.setChecked(True)
        self.ocr_checkbox.setToolTip(
            "Intenta leer PDFs escaneados usando Tesseract OCR local. "
            "Es mas lento y requiere Tesseract instalado."
        )
        self.search_button.clicked.connect(self._run_search)
        self.add_pdf_button.clicked.connect(self._add_pdf)
        self.add_folder_button.clicked.connect(self._add_image_folder)
        self.library_button.clicked.connect(self._open_library_dialog)
        self.license_button.clicked.connect(self._show_license_status)

        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.search_button)
        search_row.addWidget(self.add_pdf_button)
        search_row.addWidget(self.add_folder_button)
        search_row.addWidget(self.library_button)
        search_row.addWidget(self.license_button)
        search_row.addWidget(self.ocr_checkbox)
        top_layout.addLayout(search_row)
        root.addWidget(top_panel)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_results_panel())
        splitter.addWidget(self._build_preview_panel())
        splitter.setSizes([760, 560])
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        self.setCentralWidget(central)

    def _build_results_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QLabel("Resultados de búsqueda")
        header.setObjectName("panelTitle")
        self.results_status = QLabel(
            "Añade tus manuales PDF o una carpeta completa para comenzar a buscar información técnica."
        )
        self.results_status.setObjectName("mutedText")

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setObjectName("resultsScroll")
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(10)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_scroll.setWidget(self.results_container)

        layout.addWidget(header)
        layout.addWidget(self.results_status)
        layout.addWidget(self.results_scroll, 1)
        return panel

    def _build_preview_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("previewPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.preview_title = QLabel("Vista previa")
        self.preview_title.setObjectName("panelTitle")
        self.preview_hint = QLabel("Selecciona un resultado para visualizar la página del manual.")
        self.preview_hint.setObjectName("mutedText")

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setObjectName("previewScroll")
        self.preview_scroll.setWidgetResizable(False)
        self.preview_scroll.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )
        self.preview_label = QLabel("Sin página seleccionada.")
        self.preview_label.setObjectName("previewLabel")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.preview_label.setMinimumSize(420, 540)
        self.preview_scroll.setWidget(self.preview_label)

        layout.addWidget(self.preview_title)
        layout.addWidget(self.preview_hint)
        layout.addWidget(self.preview_scroll, 1)
        return panel

    def _load_manuals(self) -> None:
        manuals = self.database.list_manuals()
        self.library_button.setText(f"Gestionar biblioteca ({len(manuals)})")

    @staticmethod
    def _track_page_stats(pages, stats: dict[str, int]):
        for page in pages:
            stats["pages"] += 1
            if page.text.strip():
                stats["text_pages"] += 1
            yield page

    def _add_pdf(self) -> None:
        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar PDF",
            str(Path.home()),
            "Archivos PDF (*.pdf)",
        )
        if not selected_file:
            return

        source_path = Path(selected_file)
        if source_path.suffix.lower() != ".pdf":
            QMessageBox.warning(self, "Archivo no válido", "Selecciona un archivo PDF.")
            return

        try:
            file_hash = self.pdf_processor.calculate_sha256(source_path)
            existing = self.database.get_manual_by_hash(file_hash)
            if existing:
                QMessageBox.information(
                    self,
                    "PDF ya añadido",
                    f"Este PDF ya está en la biblioteca:\n{existing.display_title}",
                )
                self._select_manual_in_list(existing.id)
                return

            dialog = MetadataDialog(source_path, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            metadata = dialog.metadata()
            self._set_busy(True, "Copiando PDF a la biblioteca local...")
            stored_path = self.pdf_processor.copy_pdf_to_library(
                source_path,
                self.database.manuals_dir,
            )

            use_ocr = self.ocr_checkbox.isChecked()
            self.statusBar().showMessage(
                "Extrayendo texto página por página..."
                if not use_ocr
                else "Extrayendo texto y aplicando OCR local si hace falta..."
            )
            stats = {"pages": 0, "text_pages": 0}
            pages = self._track_page_stats(
                self.pdf_processor.iter_pages(
                    stored_path,
                    use_ocr=use_ocr,
                    progress_callback=self._extraction_progress,
                ),
                stats,
            )
            manual_id = self.database.add_manual(
                metadata=metadata,
                source_path=source_path,
                stored_path=stored_path,
                file_hash=file_hash,
                pages=pages,
            )

            if stats["pages"]:
                try:
                    self.pdf_viewer.get_preview_path(stored_path, manual_id, 1)
                except Exception:
                    logger.exception("No se pudo crear la preview inicial")

            self._load_manuals()
            self._select_manual_in_list(manual_id)

            if not stats["text_pages"]:
                extra = (
                    "\n\nOCR local no está disponible ahora mismo. Instala Tesseract "
                    "OCR y después usa Reindexar con 'OCR local' activado."
                    if use_ocr and not self.pdf_processor.is_ocr_available()
                    else ""
                )
                QMessageBox.warning(
                    self,
                    "PDF añadido sin texto",
                    "El PDF se guardó, pero no se detectó texto indexable. "
                    "Puede ser un documento escaneado sin capa de texto."
                    + extra,
                )
            else:
                QMessageBox.information(
                    self,
                    "PDF añadido",
                    "El manual se copió, se extrajo el texto y quedó indexado.",
                )
        except sqlite3.IntegrityError:
            logger.exception("Intento de duplicar un manual")
            QMessageBox.warning(
                self,
                "PDF duplicado",
                "Este PDF parece estar ya registrado en la biblioteca.",
            )
        except PDFProcessingError as exc:
            logger.exception("Error procesando PDF")
            QMessageBox.critical(self, "Error al procesar PDF", str(exc))
        except Exception as exc:
            logger.exception("Error inesperado al añadir PDF")
            QMessageBox.critical(self, "Error inesperado", str(exc))
        finally:
            self._set_busy(False, "Listo")

    def _add_image_folder(self) -> None:
        selected_folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de imágenes",
            str(Path.home()),
        )
        if not selected_folder:
            return

        folder_path = Path(selected_folder)
        try:
            image_paths = self.pdf_processor.list_image_files(folder_path)
            if not image_paths:
                QMessageBox.warning(
                    self,
                    "Carpeta sin imágenes",
                    "La carpeta no contiene JPG, PNG, BMP, TIFF o WEBP.",
                )
                return

            file_hash = self.pdf_processor.calculate_image_folder_hash(image_paths)
            existing = self.database.get_manual_by_hash(file_hash)
            if existing:
                QMessageBox.information(
                    self,
                    "Carpeta ya anadida",
                    f"Esta carpeta ya está en la biblioteca:\n{existing.display_title}",
                )
                self._select_manual_in_list(existing.id)
                return

            dialog = MetadataDialog(
                folder_path,
                self,
                default_category="Reparación general",
                source_type="image_folder",
            )
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            metadata = dialog.metadata()
            output_name = f"{folder_path.name}.pdf"
            stored_path = self.pdf_processor.unique_destination(
                output_name,
                self.database.manuals_dir,
            )

            self._set_busy(True, "Convirtiendo imágenes a PDF local...")
            self.pdf_processor.create_pdf_from_images(
                image_paths,
                stored_path,
                progress_callback=self._image_conversion_progress,
            )

            self.statusBar().showMessage(
                "Aplicando OCR local a la carpeta convertida a PDF..."
            )
            stats = {"pages": 0, "text_pages": 0}
            pages = self._track_page_stats(
                self.pdf_processor.iter_pages(
                    stored_path,
                    use_ocr=True,
                    progress_callback=self._extraction_progress,
                ),
                stats,
            )
            manual_id = self.database.add_manual(
                metadata=metadata,
                source_path=folder_path,
                stored_path=stored_path,
                file_hash=file_hash,
                pages=pages,
            )

            if stats["pages"]:
                try:
                    self.pdf_viewer.get_preview_path(stored_path, manual_id, 1)
                except Exception:
                    logger.exception("No se pudo crear la preview inicial")

            self._load_manuals()
            self._select_manual_in_list(manual_id)

            if not stats["text_pages"]:
                extra = (
                    "\n\nInstala Tesseract OCR o revisa data/tessdata para poder "
                    "indexar imágenes escaneadas."
                    if not self.pdf_processor.is_ocr_available()
                    else ""
                )
                QMessageBox.warning(
                    self,
                    "PDF creado sin texto",
                    "La carpeta se convirtió a PDF, pero no se detectó texto buscable."
                    + extra,
                )
            else:
                QMessageBox.information(
                    self,
                    "Carpeta anadida",
                    "Las imágenes se convirtieron a PDF, se aplicó OCR y quedaron indexadas.",
                )
        except sqlite3.IntegrityError:
            logger.exception("Intento de duplicar una carpeta de imágenes")
            QMessageBox.warning(
                self,
                "Carpeta duplicada",
                "Esta carpeta de imágenes parece estar ya registrada.",
            )
        except PDFProcessingError as exc:
            logger.exception("Error procesando carpeta de imágenes")
            QMessageBox.critical(self, "Error al procesar carpeta", str(exc))
        except Exception as exc:
            logger.exception("Error inesperado al añadir carpeta")
            QMessageBox.critical(self, "Error inesperado", str(exc))
        finally:
            self._set_busy(False, "Listo")

    def _run_search(self) -> None:
        query = self.search_edit.text().strip()
        self._clear_results()
        if not query:
            self.results_status.setText("Escribe una palabra o frase para buscar.")
            return

        try:
            results = self.search_engine.search(query, limit=80)
        except sqlite3.OperationalError as exc:
            logger.exception("Error en búsqueda FTS")
            QMessageBox.critical(
                self,
                "Error de búsqueda",
                f"No se pudo ejecutar la búsqueda:\n{exc}",
            )
            return
        except Exception as exc:
            logger.exception("Error inesperado en búsqueda")
            QMessageBox.critical(self, "Error de búsqueda", str(exc))
            return

        if not results:
            self.results_status.setText("No se encontraron resultados.")
            self._show_preview_message("No hay página para mostrar.")
            return

        suffix = "resultado" if len(results) == 1 else "resultados"
        self.results_status.setText(f"{len(results)} {suffix} encontrados.")
        for result in results:
            card = SearchResultCard(result)
            card.selected.connect(self._select_result)
            card.view_requested.connect(self._select_result)
            card.open_requested.connect(self._open_result_pdf)
            self.results_layout.addWidget(card)
            self.result_cards.append(card)

        self._select_result(results[0])

    def _select_result(self, result: SearchResult) -> None:
        for card in self.result_cards:
            card.set_selected(card.result.page_id == result.page_id)
        self._show_preview(result)

    def _show_preview(self, result: SearchResult) -> None:
        try:
            preview_path = self.pdf_viewer.get_preview_path(
                result.stored_path,
                result.manual_id,
                result.page_number,
            )
            pixmap = QPixmap(str(preview_path))
            if pixmap.isNull():
                raise RuntimeError("La imagen de preview no se pudo cargar.")

            self.preview_title.setText(
                f"{result.display_title} - página {result.page_number}"
            )
            self.preview_hint.setText(result.metadata_summary or "Preview de página")
            self.preview_label.setText("")
            self.preview_label.setPixmap(pixmap)
            self.preview_label.resize(pixmap.size())
        except Exception as exc:
            logger.exception("No se pudo mostrar preview")
            self._show_preview_message(f"No se pudo renderizar la página:\n{exc}")

    def _preview_manual(self, manual_id: int) -> None:
        manual = self.database.get_manual(manual_id)
        if manual is None:
            return
        try:
            preview_path = self.pdf_viewer.get_preview_path(
                manual.stored_path,
                manual.id,
                1,
            )
            pixmap = QPixmap(str(preview_path))
            if pixmap.isNull():
                raise RuntimeError("La preview no se pudo cargar.")
            self.preview_title.setText(f"{manual.display_title} - página 1")
            self.preview_hint.setText(manual.metadata_summary or "Primera página")
            self.preview_label.setText("")
            self.preview_label.setPixmap(pixmap)
            self.preview_label.resize(pixmap.size())
        except Exception:
            logger.exception("No se pudo previsualizar el manual seleccionado")
            self._show_preview_message("No se pudo generar la preview de este manual.")

    def _open_result_pdf(self, result: SearchResult) -> None:
        try:
            self.pdf_viewer.open_pdf(result.stored_path, result.page_number)
        except Exception as exc:
            logger.exception("No se pudo abrir PDF")
            QMessageBox.critical(self, "No se pudo abrir el PDF", str(exc))

    def _open_library_dialog(self) -> None:
        dialog = LibraryDialog(
            database=self.database,
            pdf_viewer=self.pdf_viewer,
            reindex_callback=self._reindex_all,
            changed_callback=self._library_changed,
            parent=self,
        )
        dialog.exec()

    def _show_license_status(self) -> None:
        QMessageBox.information(
            self,
            "Estado de licencia",
            "\n".join(
                [
                    f"Producto: {self.license_status.product}",
                    f"Estado: {self.license_status.state_label}",
                    f"Tipo de licencia: {self.license_status.license_type}",
                ]
            ),
        )

    def _library_changed(self) -> None:
        self._load_manuals()
        self._clear_results()
        self._show_preview_message("Biblioteca actualizada.")

    def _reindex_all(self) -> None:
        manuals = self.database.list_manuals()
        if not manuals:
            QMessageBox.information(
                self,
                "Sin manuales",
                "Todavía no hay manuales para reindexar.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Reindexar biblioteca",
            "Se volverá a extraer el texto de todos los PDFs almacenados. ¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        processed = 0
        failures = 0
        self._set_busy(True, "Reindexando biblioteca...")
        try:
            for manual in manuals:
                try:
                    pages = self._track_page_stats(
                        self.pdf_processor.iter_pages(
                            manual.stored_path,
                            use_ocr=self.ocr_checkbox.isChecked(),
                            progress_callback=self._extraction_progress,
                        ),
                        {"pages": 0, "text_pages": 0},
                    )
                    self.database.replace_pages(manual.id, pages)
                    self.pdf_viewer.clear_previews_for_manual(manual.id)
                    processed += 1
                except Exception:
                    failures += 1
                    logger.exception("No se pudo reindexar manual id=%s", manual.id)
            if processed:
                self.database.optimize_search_index()
        finally:
            self._set_busy(False, "Listo")

        QMessageBox.information(
            self,
            "Reindexado finalizado",
            f"Manuales reindexados: {processed}\nErrores: {failures}",
        )

    def _clear_results(self) -> None:
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.result_cards.clear()

    def _show_preview_message(self, message: str) -> None:
        self.preview_title.setText("Vista previa")
        self.preview_hint.setText("")
        self.preview_label.clear()
        self.preview_label.setText(message)
        self.preview_label.setMinimumSize(420, 540)
        self.preview_label.resize(420, 540)

    def _select_manual_in_list(self, manual_id: int) -> None:
        self._preview_manual(manual_id)

    def _set_busy(self, busy: bool, message: str) -> None:
        if busy:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.statusBar().showMessage(message)
        else:
            if QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()
            self.statusBar().showMessage(message)

    def _extraction_progress(self, page_number: int, total_pages: int) -> None:
        self.statusBar().showMessage(
            f"Procesando página {page_number} de {total_pages}..."
        )
        QApplication.processEvents()

    def _image_conversion_progress(self, image_number: int, total_images: int) -> None:
        self.statusBar().showMessage(
            f"Convirtiendo imagen {image_number} de {total_images} a PDF..."
        )
        QApplication.processEvents()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background: #f5f7fb;
                color: #111827;
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 10.5pt;
            }
            #topPanel {
                background: #ffffff;
                border-bottom: 1px solid #d0d5dd;
            }
            #appTitle {
                background: #ffffff;
                color: #101828;
                font-size: 26px;
                font-weight: 700;
            }
            #appSubtitle {
                background: #ffffff;
                color: #667085;
                font-size: 12px;
                font-weight: 500;
            }
            #brandLogo {
                background: #ffffff;
                border: none;
            }
            #sidePanel, #contentPanel, #previewPanel {
                background: #f5f7fb;
            }
            #panelTitle {
                color: #101828;
                font-size: 15px;
                font-weight: 700;
            }
            #mutedText, #resultMeta {
                color: #667085;
            }
            QLineEdit, QTextEdit, QComboBox {
                background: #ffffff;
                border: 1px solid #cfd4dc;
                border-radius: 6px;
                padding: 8px;
                selection-background-color: #2563eb;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QCheckBox {
                background: #ffffff;
                color: #344054;
                padding: 7px 8px;
                border: 1px solid #cfd4dc;
                border-radius: 6px;
            }
            QPushButton {
                background: #2563eb;
                border: 1px solid #1d4ed8;
                border-radius: 6px;
                color: #ffffff;
                font-weight: 600;
                padding: 8px 13px;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            QPushButton#secondaryButton {
                background: #ffffff;
                border: 1px solid #cfd4dc;
                color: #1f2937;
                padding: 6px 10px;
            }
            QPushButton#secondaryButton:hover {
                background: #eef2f7;
            }
            QPushButton#dangerButton {
                background: #ffffff;
                border: 1px solid #fda29b;
                color: #b42318;
            }
            QPushButton#dangerButton:hover {
                background: #fff1f0;
            }
            QListWidget#manualList {
                background: #ffffff;
                border: 1px solid #d0d5dd;
                border-radius: 8px;
                padding: 6px;
            }
            QListWidget#manualList::item {
                border-radius: 6px;
                padding: 9px;
                margin: 2px;
            }
            QListWidget#manualList::item:selected {
                background: #e0edff;
                color: #101828;
            }
            QScrollArea#resultsScroll, QScrollArea#previewScroll {
                background: transparent;
                border: none;
            }
            QFrame#resultCard {
                background: #ffffff;
                border: 1px solid #d0d5dd;
                border-radius: 8px;
            }
            QFrame#resultCard:hover {
                border-color: #98a2b3;
            }
            QFrame#resultCard[selected="true"] {
                background: #eff6ff;
                border: 2px solid #2563eb;
            }
            QLabel#resultSnippet {
                color: #344054;
                line-height: 1.35;
            }
            QLabel#previewLabel {
                background: #ffffff;
                border: 1px solid #d0d5dd;
                border-radius: 8px;
                color: #667085;
                padding: 18px;
            }
            QSplitter::handle {
                background: #e4e7ec;
            }
            """
        )
