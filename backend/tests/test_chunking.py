"""Unit tests for code chunking (pure functions — no DB, no network).

Needs the tree-sitter grammar packages, so run inside the container:
    docker compose exec api pip install -r requirements-dev.txt
    docker compose exec api pytest -q tests/test_chunking.py
"""
import pytest

from app.enums import SymbolType
from app.services.ingest.chunking import chunk_file, chunk_source, detect_language
from app.services.ingest.chunking import fallback as fallback_module
from app.services.ingest.chunking.fallback import FallbackChunker


# --- language detection -----------------------------------------------------

@pytest.mark.parametrize(
    "path,language",
    [
        ("app/services/auth.py", "python"),
        ("x.js", "javascript"),
        ("x.jsx", "javascript"),
        ("x.mjs", "javascript"),
        ("x.cjs", "javascript"),
        ("x.ts", "typescript"),
        ("x.tsx", "tsx"),
        ("README.md", None),
        ("Dockerfile", None),
    ],
)
def test_detect_language(path, language):
    assert detect_language(path) == language


# --- tree-sitter AST chunking ----------------------------------------------

def test_python_symbols_and_line_spans():
    src = (
        "def top():\n"          # line 1-2
        "    return 1\n"
        "\n"
        "class Auth:\n"         # line 4
        "    def login(self):\n"  # line 5-6 (method)
        "        return 2\n"
    )
    by_name = {p.symbol_name: p for p in chunk_source(src, "python")}

    assert by_name["top"].symbol_type == SymbolType.FUNCTION
    assert by_name["Auth"].symbol_type == SymbolType.CLASS
    assert by_name["login"].symbol_type == SymbolType.METHOD

    assert (by_name["top"].start_line, by_name["top"].end_line) == (1, 2)
    assert by_name["login"].start_line == 5
    assert by_name["login"].language == "python"


def test_javascript_function_class_method():
    src = "function foo() { return 1; }\nclass A { bar() { return 2; } }\n"
    got = {(p.symbol_name, p.symbol_type) for p in chunk_source(src, "javascript")}
    assert ("foo", SymbolType.FUNCTION) in got
    assert ("A", SymbolType.CLASS) in got
    assert ("bar", SymbolType.METHOD) in got


def test_typescript_interface_and_function():
    src = "interface Shape { x: number; }\nfunction area(): number { return 1; }\n"
    names = {p.symbol_name for p in chunk_source(src, "typescript")}
    assert {"Shape", "area"} <= names


# --- fallback ---------------------------------------------------------------

def test_unsupported_language_uses_fallback():
    pieces = chunk_source("a\nb\nc\n", None)
    assert len(pieces) == 1
    piece = pieces[0]
    assert piece.symbol_name is None and piece.symbol_type is None
    assert (piece.start_line, piece.end_line) == (1, 3)


def test_python_without_definitions_falls_back():
    pieces = chunk_source("x = 1\ny = 2\nprint(x + y)\n", "python")
    assert len(pieces) == 1
    assert pieces[0].symbol_type is None  # a fallback window, not a symbol


def test_empty_source_returns_no_chunks():
    assert chunk_source("", "python") == []
    assert chunk_source("", None) == []


def test_fallback_windows_and_overlap(monkeypatch):
    # step = 3 - 1 = 2; 7 lines -> windows starting at line 1, 3, 5
    monkeypatch.setattr(fallback_module, "FALLBACK_CHUNK_LINES", 3)
    monkeypatch.setattr(fallback_module, "FALLBACK_OVERLAP_LINES", 1)
    src = "\n".join(str(i) for i in range(1, 8)) + "\n"  # 7 lines
    spans = [(p.start_line, p.end_line) for p in FallbackChunker().chunk(src, None)]
    assert spans == [(1, 3), (3, 5), (5, 7)]


# --- chunk_file (reads from disk) WILL TEST LATER ------------------------------------------

def test_chunk_file_reads_and_detects(tmp_path):
    path = tmp_path / "m.py"
    path.write_text("def f():\n    return 1\n")
    pieces = chunk_file(path, "m.py")
    assert any(p.symbol_name == "f" and p.symbol_type == SymbolType.FUNCTION for p in pieces)


def test_chunk_file_binary_returns_empty(tmp_path):
    path = tmp_path / "blob.bin"
    path.write_bytes(b"\x00\x01\x02\xff")
    assert chunk_file(path, "blob.bin") == []
