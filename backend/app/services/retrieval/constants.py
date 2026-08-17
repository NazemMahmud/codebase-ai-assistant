"""Constants for hybrid retrieval."""

# tsvector config — must match how content_tsv is generated (migration uses 'simple').
FTS_CONFIG = "simple"
FTS_MATCH_OP = "@@"

# pg_trgm minimum similarity for a symbol_name to count as a match.
SYMBOL_SIMILARITY_THRESHOLD = 0.1
