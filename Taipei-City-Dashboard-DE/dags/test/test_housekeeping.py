import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import pytest


# Make `utils.*` importable
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DAGS_ROOT = os.path.join(REPO_ROOT, "Taipei-City-Dashboard-DE", "dags")
if DAGS_ROOT not in sys.path:
    sys.path.insert(0, DAGS_ROOT)

from utils.housekeeping import (  # noqa: E402
    HousekeepingConfig,
    PostgresHousekeeper,
    _normalize_table_names,
    _parse_table_name,
)


class _StubResult:
    def __init__(self, rows: List[Tuple[Any, ...]]):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class _StubConn:
    def __init__(
        self,
        *,
        schema: str,
        table: str,
        existing_indexes: List[Tuple[str, str]],
        index_exists: bool = False,
        statements: Optional[List[str]] = None,
    ):
        self.schema = schema
        self.table = table
        self.existing_indexes = existing_indexes
        self.index_exists = index_exists
        self.statements = statements if statements is not None else []

    def execute(self, clause, params: Optional[Dict[str, Any]] = None):
        sql_text = getattr(clause, "text", None)
        if sql_text is None:
            sql_text = str(clause)
        sql_text = " ".join(sql_text.split())

        # Simulate pg_indexes lookup
        if "FROM pg_indexes" in sql_text:
            assert params == {"schema": self.schema, "table": self.table}
            return _StubResult([(n, d) for (n, d) in self.existing_indexes])

        # Simulate pg_class lookup
        if "FROM pg_class" in sql_text and "relkind = 'i'" in sql_text:
            assert params == {"schema": self.schema, "index": params["index"]}
            return _StubResult([(1,)] if self.index_exists else [])

        self.statements.append(sql_text)
        return _StubResult([])


class _BeginCtx:
    def __init__(self, conn: _StubConn):
        self._conn = conn

    def __enter__(self):
        return self._conn

    def __exit__(self, exc_type, exc, tb):
        return False


class _StubEngine:
    def __init__(self, begin_conn: _StubConn, vacuum_statements: List[str]):
        self._begin_conn = begin_conn
        self._vacuum_statements = vacuum_statements

    def begin(self):
        return _BeginCtx(self._begin_conn)

    def connect(self):
        return self

    def execution_options(self, **kwargs):
        # Expect AUTOCOMMIT for VACUUM
        return self

    def execute(self, clause):
        sql_text = getattr(clause, "text", None)
        if sql_text is None:
            sql_text = str(clause)
        sql_text = " ".join(sql_text.split())
        self._vacuum_statements.append(sql_text)
        return _StubResult([])

    def close(self):
        return None


def test_parse_table_name_default_schema():
    assert _parse_table_name("my_table") == ("public", "my_table")


def test_parse_table_name_with_schema():
    assert _parse_table_name("custom.my_table") == ("custom", "my_table")


def test_normalize_table_names():
    assert _normalize_table_names("t") == ["t"]
    assert _normalize_table_names(["t1", "", "t2"]) == ["t1", "t2"]


def test_cleanup_preserves_existing_indexes_and_vacuum():
    schema, table = "public", "t"
    existing = [("idx_existing", f'CREATE INDEX "idx_existing" ON "{schema}"."{table}" ("x")')]

    statements: List[str] = []
    vacuum_statements: List[str] = []

    conn = _StubConn(schema=schema, table=table, existing_indexes=existing, statements=statements)
    engine = _StubEngine(conn, vacuum_statements)

    cfg = HousekeepingConfig(
        retention_months=6,
        time_column="data_time",
        default_schema=schema,
        create_index=True,
        preserve_existing_indexes=True,
        vacuum_analyze=True,
    )
    hk = PostgresHousekeeper(cfg)

    processed = hk.cleanup_table(engine, f"{schema}.{table}")
    assert processed == 1

    create_index_sql = [s for s in statements if s.upper().startswith("CREATE INDEX")]
    assert create_index_sql == ['CREATE INDEX "idx_existing" ON "public"."t" ("x")']

    assert any(s.upper().startswith("VACUUM (ANALYZE)") for s in vacuum_statements)


def test_cleanup_fallback_index_when_no_existing_indexes():
    schema, table = "public", "t2"

    statements: List[str] = []
    vacuum_statements: List[str] = []

    conn = _StubConn(schema=schema, table=table, existing_indexes=[], statements=statements)
    engine = _StubEngine(conn, vacuum_statements)

    cfg = HousekeepingConfig(
        retention_months=6,
        time_column="data_time",
        default_schema=schema,
        create_index=True,
        preserve_existing_indexes=True,
        vacuum_analyze=False,
    )
    hk = PostgresHousekeeper(cfg)

    processed = hk.cleanup_table(engine, f"{schema}.{table}")
    assert processed == 1

    create_index_sql = [s for s in statements if s.upper().startswith("CREATE INDEX")]
    assert any("IF NOT EXISTS" in s.upper() for s in create_index_sql)
