from __future__ import annotations

import logging
import re

from .database import Database
from .models import SearchResult


logger = logging.getLogger(__name__)
TOKEN_RE = re.compile(r"[\wÀ-ÖØ-öø-ÿ]+", re.UNICODE)


class SearchEngine:
    def __init__(self, database: Database) -> None:
        self.database = database

    def search(self, query: str, limit: int = 50) -> list[SearchResult]:
        fts_query = self.build_fts_query(query)
        if not fts_query:
            return []
        logger.info("Busqueda FTS: %s", fts_query)
        return self.database.search_pages(fts_query, limit=limit)

    @staticmethod
    def build_fts_query(query: str) -> str:
        raw_query = query.strip()
        if not raw_query:
            return ""

        exact_phrase = len(raw_query) >= 2 and raw_query[0] == raw_query[-1] == '"'
        searchable_text = raw_query[1:-1] if exact_phrase else raw_query
        tokens = TOKEN_RE.findall(searchable_text)
        if not tokens:
            return ""

        escaped_tokens = [token.replace('"', '""') for token in tokens]
        if exact_phrase and len(escaped_tokens) > 1:
            return f'"{" ".join(escaped_tokens)}"'
        return " AND ".join(f'"{token}"' for token in escaped_tokens)
