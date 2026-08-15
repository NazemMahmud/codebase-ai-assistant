"""Constants for code chunking — languages, AST node maps, fallback sizes."""
from app.enums import SymbolType

LANGUAGE_PYTHON = "python"
LANGUAGE_JAVASCRIPT = "javascript"
LANGUAGE_TYPESCRIPT = "typescript"
LANGUAGE_TSX = "tsx"

# File extension -> language name.
EXTENSION_TO_LANGUAGE = {
    ".py": LANGUAGE_PYTHON,
    ".js": LANGUAGE_JAVASCRIPT,
    ".jsx": LANGUAGE_JAVASCRIPT,
    ".mjs": LANGUAGE_JAVASCRIPT,
    ".cjs": LANGUAGE_JAVASCRIPT,
    ".ts": LANGUAGE_TYPESCRIPT,
    ".tsx": LANGUAGE_TSX,
}

# Languages handled by the tree-sitter (AST) chunker; everything else -> fallback.
TREE_SITTER_LANGUAGES = {
    LANGUAGE_PYTHON, LANGUAGE_JAVASCRIPT, LANGUAGE_TYPESCRIPT, LANGUAGE_TSX,
}

# AST node type -> SymbolType, per language. Adding a language = add a grammar
# package + an entry here (the extension seam).
DEFINITION_TYPES = {
    LANGUAGE_PYTHON: {
        "function_definition": SymbolType.FUNCTION,
        "class_definition": SymbolType.CLASS,
    },
    LANGUAGE_JAVASCRIPT: {
        "function_declaration": SymbolType.FUNCTION,
        "generator_function_declaration": SymbolType.FUNCTION,
        "class_declaration": SymbolType.CLASS,
        "method_definition": SymbolType.METHOD,
    },
    LANGUAGE_TYPESCRIPT: {
        "function_declaration": SymbolType.FUNCTION,
        "generator_function_declaration": SymbolType.FUNCTION,
        "class_declaration": SymbolType.CLASS,
        "abstract_class_declaration": SymbolType.CLASS,
        "interface_declaration": SymbolType.CLASS,
        "enum_declaration": SymbolType.CLASS,
        "method_definition": SymbolType.METHOD,
    },
}
# TSX shares TypeScript's node types.
DEFINITION_TYPES[LANGUAGE_TSX] = DEFINITION_TYPES[LANGUAGE_TYPESCRIPT]

# The tree-sitter field holding a definition's name; Python funcs nested in a
# class body are treated as methods.
NODE_NAME_FIELD = "name"
PYTHON_FUNCTION_NODE = "function_definition"

TEXT_ENCODING = "utf-8"

# Fallback line-window splitter (unsupported languages / files with no symbols).
FALLBACK_CHUNK_LINES = 200
FALLBACK_OVERLAP_LINES = 20
