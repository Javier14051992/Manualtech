from __future__ import annotations

from dataclasses import dataclass


def compact_metadata(*values: str | int | None) -> str:
    parts = [str(value).strip() for value in values if str(value or "").strip()]
    return " - ".join(parts)


@dataclass(frozen=True)
class ManualMetadata:
    title: str = ""
    document_category: str = ""
    topic: str = ""
    brand: str = ""
    model: str = ""
    year: str = ""
    engine: str = ""
    system: str = ""
    document_type: str = ""
    language: str = ""
    notes: str = ""
    source_type: str = "pdf"

    def title_or(self, fallback: str) -> str:
        return self.title.strip() or fallback


@dataclass(frozen=True)
class Manual:
    id: int
    filename: str
    original_path: str
    stored_path: str
    title: str
    document_category: str = ""
    topic: str = ""
    brand: str = ""
    model: str = ""
    year: str = ""
    engine: str = ""
    system: str = ""
    document_type: str = ""
    language: str = ""
    notes: str = ""
    source_type: str = "pdf"
    created_at: str = ""
    file_hash: str = ""

    @property
    def display_title(self) -> str:
        return self.title.strip() or self.filename

    @property
    def metadata_summary(self) -> str:
        vehicle = compact_metadata(self.brand, self.model, self.year)
        return compact_metadata(
            self.document_category,
            self.topic,
            vehicle,
            self.system,
        )


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class SearchResult:
    page_id: int
    manual_id: int
    page_number: int
    title: str
    filename: str
    stored_path: str
    document_category: str = ""
    topic: str = ""
    brand: str = ""
    model: str = ""
    year: str = ""
    engine: str = ""
    system: str = ""
    document_type: str = ""
    language: str = ""
    notes: str = ""
    source_type: str = "pdf"
    snippet: str = ""
    rank: float = 0.0

    @property
    def display_title(self) -> str:
        return self.title.strip() or self.filename

    @property
    def metadata_summary(self) -> str:
        vehicle = compact_metadata(self.brand, self.model, self.year)
        return compact_metadata(
            self.document_category,
            self.topic,
            vehicle,
            self.system,
        )
