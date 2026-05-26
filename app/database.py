from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .models import Manual, ManualMetadata, PageText, SearchResult


logger = logging.getLogger(__name__)


class Database:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.manuals_dir = self.data_dir / "manuales"
        self.previews_dir = self.data_dir / "previews"
        self.logs_dir = self.base_dir / "logs"
        self.db_path = self.data_dir / "manuales.db"

        self.ensure_directories()
        self.initialize()

    def ensure_directories(self) -> None:
        for directory in (self.data_dir, self.manuals_dir, self.previews_dir, self.logs_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA cache_size = -64000")
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS manuals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    original_path TEXT,
                    stored_path TEXT NOT NULL UNIQUE,
                    title TEXT,
                    document_category TEXT,
                    topic TEXT,
                    brand TEXT,
                    model TEXT,
                    year TEXT,
                    engine TEXT,
                    system TEXT,
                    document_type TEXT,
                    language TEXT,
                    notes TEXT,
                    source_type TEXT DEFAULT 'pdf',
                    file_hash TEXT UNIQUE,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manual_id INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    text TEXT,
                    FOREIGN KEY (manual_id) REFERENCES manuals(id) ON DELETE CASCADE,
                    UNIQUE (manual_id, page_number)
                );

                CREATE INDEX IF NOT EXISTS idx_pages_manual_id
                    ON pages (manual_id);

                CREATE INDEX IF NOT EXISTS idx_manuals_created_at
                    ON manuals (created_at);
                """
            )
            self._ensure_fts_table(conn)
            self._ensure_manual_columns(conn)
            conn.commit()

    def _ensure_fts_table(self, conn: sqlite3.Connection) -> None:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'pages_fts'"
        ).fetchone()
        if row is not None:
            sql = (row["sql"] or "").lower()
            columns = [
                column["name"]
                for column in conn.execute("PRAGMA table_info(pages_fts)")
            ]
            uses_external_content = (
                "content='pages'" in sql
                or 'content="pages"' in sql
                or "content=pages" in sql
            )
            if columns == ["text"] and uses_external_content:
                return

            logger.info("Migrando indice FTS5 a modo external content")
            conn.execute("DROP TABLE pages_fts")

        try:
            conn.execute(
                """
                CREATE VIRTUAL TABLE pages_fts USING fts5(
                    text,
                    content='pages',
                    content_rowid='id',
                    tokenize = 'unicode61 remove_diacritics 2'
                );
                """
            )
        except sqlite3.OperationalError as exc:
            raise RuntimeError(
                "La instalación de SQLite de este Python no tiene FTS5 habilitado."
            ) from exc

        conn.execute(
            """
            INSERT INTO pages_fts (rowid, text)
            SELECT id, COALESCE(text, '')
            FROM pages
            """
        )

    def _ensure_manual_columns(self, conn: sqlite3.Connection) -> None:
        existing_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(manuals)")
        }
        migrations = {
            "document_category": "ALTER TABLE manuals ADD COLUMN document_category TEXT",
            "topic": "ALTER TABLE manuals ADD COLUMN topic TEXT",
            "source_type": "ALTER TABLE manuals ADD COLUMN source_type TEXT DEFAULT 'pdf'",
        }
        for column, statement in migrations.items():
            if column not in existing_columns:
                conn.execute(statement)
                logger.info("Columna de manuales añadida: %s", column)

    def add_manual(
        self,
        metadata: ManualMetadata,
        source_path: Path,
        stored_path: Path,
        file_hash: str,
        pages: Iterable[PageText],
    ) -> int:
        stored_path = Path(stored_path)
        title = metadata.title_or(stored_path.stem)
        created_at = datetime.now().isoformat(timespec="seconds")

        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO manuals (
                    filename, original_path, stored_path, title, document_category,
                    topic, brand, model, year, engine, system, document_type,
                    language, notes, source_type, file_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stored_path.name,
                    str(Path(source_path).resolve()),
                    str(stored_path.resolve()),
                    title,
                    metadata.document_category,
                    metadata.topic,
                    metadata.brand,
                    metadata.model,
                    metadata.year,
                    metadata.engine,
                    metadata.system,
                    metadata.document_type,
                    metadata.language,
                    metadata.notes,
                    metadata.source_type,
                    file_hash,
                    created_at,
                ),
            )
            manual_id = int(cursor.lastrowid)
            self._insert_pages(conn, manual_id, pages)
            conn.commit()

        logger.info("Manual añadido: %s", stored_path.name)
        return manual_id

    def _insert_pages(
        self,
        conn: sqlite3.Connection,
        manual_id: int,
        pages: Iterable[PageText],
    ) -> None:
        for page in pages:
            text = page.text or ""
            cursor = conn.execute(
                """
                INSERT INTO pages (manual_id, page_number, text)
                VALUES (?, ?, ?)
                """,
                (manual_id, page.page_number, text),
            )
            page_id = int(cursor.lastrowid)
            conn.execute(
                """
                INSERT INTO pages_fts (rowid, text)
                VALUES (?, ?)
                """,
                (page_id, text),
            )

    def replace_pages(self, manual_id: int, pages: Iterable[PageText]) -> None:
        with self.connect() as conn:
            page_ids = [
                int(row["id"])
                for row in conn.execute(
                    "SELECT id FROM pages WHERE manual_id = ?", (manual_id,)
                )
            ]
            if page_ids:
                conn.executemany(
                    "DELETE FROM pages_fts WHERE rowid = ?",
                    [(page_id,) for page_id in page_ids],
                )
            conn.execute("DELETE FROM pages WHERE manual_id = ?", (manual_id,))
            self._insert_pages(conn, manual_id, pages)
            conn.commit()
        logger.info("Manual reindexado: id=%s", manual_id)

    def list_manuals(self) -> list[Manual]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM manuals
                ORDER BY datetime(created_at) DESC, title COLLATE NOCASE ASC
                """
            ).fetchall()
        return [self._row_to_manual(row) for row in rows]

    def get_manual(self, manual_id: int) -> Manual | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM manuals WHERE id = ?", (manual_id,)
            ).fetchone()
        return self._row_to_manual(row) if row else None

    def get_manual_by_hash(self, file_hash: str) -> Manual | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM manuals WHERE file_hash = ?", (file_hash,)
            ).fetchone()
        return self._row_to_manual(row) if row else None

    def delete_manual(self, manual_id: int) -> Manual | None:
        manual = self.get_manual(manual_id)
        if manual is None:
            return None

        with self.connect() as conn:
            page_ids = [
                int(row["id"])
                for row in conn.execute(
                    "SELECT id FROM pages WHERE manual_id = ?", (manual_id,)
                )
            ]
            if page_ids:
                conn.executemany(
                    "DELETE FROM pages_fts WHERE rowid = ?",
                    [(page_id,) for page_id in page_ids],
                )
            conn.execute("DELETE FROM manuals WHERE id = ?", (manual_id,))
            conn.commit()

        logger.info("Manual eliminado de la base de datos: id=%s", manual_id)
        return manual

    def search_pages(self, fts_query: str, limit: int = 50) -> list[SearchResult]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    p.id AS page_id,
                    p.page_number AS page_number,
                    m.id AS manual_id,
                    m.filename AS filename,
                    m.stored_path AS stored_path,
                    m.title AS title,
                    m.document_category AS document_category,
                    m.topic AS topic,
                    m.brand AS brand,
                    m.model AS model,
                    m.year AS year,
                    m.engine AS engine,
                    m.system AS system,
                    m.document_type AS document_type,
                    m.language AS language,
                    m.notes AS notes,
                    m.source_type AS source_type,
                    snippet(pages_fts, 0, '[[H]]', '[[/H]]', '...', 28) AS snippet,
                    bm25(pages_fts) AS rank
                FROM pages_fts
                JOIN pages p ON p.id = pages_fts.rowid
                JOIN manuals m ON m.id = p.manual_id
                WHERE pages_fts MATCH ?
                ORDER BY rank ASC
                LIMIT ?
                """,
                (fts_query, limit),
            ).fetchall()

        return [self._row_to_search_result(row) for row in rows]

    def optimize_search_index(self) -> None:
        with self.connect() as conn:
            conn.execute("INSERT INTO pages_fts(pages_fts) VALUES('optimize')")
            conn.execute("PRAGMA optimize")
            conn.commit()
        logger.info("Indice FTS5 optimizado")

    @staticmethod
    def _row_to_manual(row: sqlite3.Row) -> Manual:
        return Manual(
            id=int(row["id"]),
            filename=row["filename"] or "",
            original_path=row["original_path"] or "",
            stored_path=row["stored_path"] or "",
            title=row["title"] or "",
            document_category=row["document_category"] or "",
            topic=row["topic"] or "",
            brand=row["brand"] or "",
            model=row["model"] or "",
            year=row["year"] or "",
            engine=row["engine"] or "",
            system=row["system"] or "",
            document_type=row["document_type"] or "",
            language=row["language"] or "",
            notes=row["notes"] or "",
            source_type=row["source_type"] or "pdf",
            created_at=row["created_at"] or "",
            file_hash=row["file_hash"] or "",
        )

    @staticmethod
    def _row_to_search_result(row: sqlite3.Row) -> SearchResult:
        return SearchResult(
            page_id=int(row["page_id"]),
            manual_id=int(row["manual_id"]),
            page_number=int(row["page_number"]),
            title=row["title"] or "",
            filename=row["filename"] or "",
            stored_path=row["stored_path"] or "",
            document_category=row["document_category"] or "",
            topic=row["topic"] or "",
            brand=row["brand"] or "",
            model=row["model"] or "",
            year=row["year"] or "",
            engine=row["engine"] or "",
            system=row["system"] or "",
            document_type=row["document_type"] or "",
            language=row["language"] or "",
            notes=row["notes"] or "",
            source_type=row["source_type"] or "pdf",
            snippet=row["snippet"] or "",
            rank=float(row["rank"] or 0.0),
        )
