from dataclasses import dataclass
from typing import Protocol

from app.enums import SymbolType


@dataclass
class ChunkPiece:
    """One chunk produced by a chunker, before it becomes a DB row.

    Carries what the `chunks` table needs: the code, its language,
    the symbol it represents (name + type, both optional for fallback chunks), and
    the line span for `file:line` citations. `token_count` is filled at the embed step.
    """

    content: str
    language: str | None
    symbol_name: str | None
    symbol_type: SymbolType | None
    start_line: int
    end_line: int
    token_count: int | None = None


class Chunker(Protocol):
    """Turn source text into ChunkPieces.

    a new strategy is any object with this `chunk` method;
    the dispatcher decides which one to use per language.
    """

    def chunk(self, source: str, language: str | None) -> list[ChunkPiece]: ...
