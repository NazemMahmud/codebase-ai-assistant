"""Single source of truth for table names, shared across models.

Migrations intentionally do NOT import this because,
A migration is a frozen snapshot of the schema at a point in time
And must stay decoupled from evolving app code.
"""


class TableName:
    CODEBASES = "codebases"
    CHUNKS = "chunks"
