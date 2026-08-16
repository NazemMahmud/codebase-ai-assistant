"""AST chunker — one chunk per function / class / method, via tree-sitter."""
from __future__ import annotations

from tree_sitter import Language, Node, Parser

from app.enums import SymbolType
from app.services.ingest.chunking.base import ChunkPiece
from app.services.ingest.chunking.constants import (
    DEFINITION_TYPES,
    LANGUAGE_JAVASCRIPT,
    LANGUAGE_PYTHON,
    LANGUAGE_TSX,
    LANGUAGE_TYPESCRIPT,
    NODE_NAME_FIELD,
    PYTHON_FUNCTION_NODE,
    TEXT_ENCODING,
)


def _build_languages() -> dict[str, Language]:
    """Load the grammar packages and return {language name -> tree-sitter Language}."""
    # Imported lazily: grammar packages are heavy and only needed for AST chunking.
    import tree_sitter_javascript as ts_javascript
    import tree_sitter_python as ts_python
    import tree_sitter_typescript as ts_typescript

    return {
        LANGUAGE_PYTHON: Language(ts_python.language()),
        LANGUAGE_JAVASCRIPT: Language(ts_javascript.language()),
        LANGUAGE_TYPESCRIPT: Language(ts_typescript.language_typescript()),
        LANGUAGE_TSX: Language(ts_typescript.language_tsx()),
    }


class TreeSitterChunker:
    """Structure-aware chunker for python/js/ts.

    Emits one ChunkPiece per top-level function/class and per method inside a class.
    Returns [] for unsupported languages or files with no definitions
    the dispatcher then uses the fallback splitter.
    Parsers are built lazily and cached per language.
    """

    def __init__(self) -> None:
        self._languages: dict[str, Language] | None = None
        self._parsers: dict[str, Parser] = {}

    def chunk(self, source: str, language: str | None) -> list[ChunkPiece]:
        """Parse `source` for `language` and return one ChunkPiece per definition.

        For unknown/unsupported language, returns [];
        then the dispatcher uses the fallback splitter.
        """
        if language is None:
            return []

        parser = self._get_parser(language)

        if parser is None:
            return []

        source_bytes = source.encode(TEXT_ENCODING)
        tree         = parser.parse(source_bytes)
        pieces: list[ChunkPiece] = []
        self._walk(tree.root_node, language, source_bytes, inside_class=False, out=pieces)

        return pieces

    def _get_parser(self, language: str) -> Parser | None:
        """Return a cached Parser for `language` (build on first use),
        or None if that language has no grammar.
        """
        if self._languages is None:
            self._languages = _build_languages()

        if language not in self._languages:
            return None

        if language not in self._parsers:
            self._parsers[language] = Parser(self._languages[language])

        return self._parsers[language]

    def _walk(
        self,
        node: Node,
        language: str,
        source_bytes: bytes,
        inside_class: bool,
        out: list[ChunkPiece],
    ) -> None:
        """Recursively scan the AST, appending a ChunkPiece for each definition.

        Non-definition nodes are traversed to reach nested defs; classes are
        descended into (to capture methods) but functions are not.
        """
        type_map = DEFINITION_TYPES[language]

        for child in node.children:
            symbol_type = type_map.get(child.type)

            if symbol_type is None:
                self._walk(child, language, source_bytes, inside_class, out)
                continue

            # A Python function nested in a class body is a method.
            if inside_class and child.type == PYTHON_FUNCTION_NODE:
                symbol_type = SymbolType.METHOD

            out.append(self._make_piece(child, language, source_bytes, symbol_type))

            # Descend into classes to capture their methods; not into functions.
            if symbol_type == SymbolType.CLASS:
                self._walk(child, language, source_bytes, inside_class=True, out=out)

    @staticmethod
    def _make_piece(
        node: Node, language: str, source_bytes: bytes, symbol_type: SymbolType
    ) -> ChunkPiece:
        """Build a ChunkPiece from a definition node: its source text, symbol name,
        type, and 1-indexed line span."""

        name_node   = node.child_by_field_name(NODE_NAME_FIELD)
        symbol_name = (
            name_node.text.decode(TEXT_ENCODING) if name_node is not None else None
        )
        content = source_bytes[node.start_byte : node.end_byte].decode(
            TEXT_ENCODING, errors="ignore"
        )

        return ChunkPiece(
            content=content,
            language=language,
            symbol_name=symbol_name,
            symbol_type=symbol_type,
            start_line=node.start_point[0] + 1,  # tree-sitter rows are 0-indexed
            end_line=node.end_point[0] + 1,
        )
