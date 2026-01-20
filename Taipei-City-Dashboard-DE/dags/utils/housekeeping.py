import logging
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.sql import text as sa_text

logger = logging.getLogger(__name__)


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(name: str, kind: str) -> None:
    if not isinstance(name, str) or not name:
        raise ValueError(f"{kind} must be a non-empty string")
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(
            f"Invalid {kind} '{name}'. Only letters, numbers, underscore are allowed, "
            "and it must not start with a number."
        )


def _parse_table_name(table_name: str, default_schema: str = "public") -> Tuple[str, str]:
    """Return (schema, table). Accepts 'table' or 'schema.table'."""
    if not isinstance(table_name, str) or not table_name:
        raise ValueError("table_name must be a non-empty string")

    if "." in table_name:
        schema, table = table_name.split(".", 1)
    else:
        schema, table = default_schema, table_name

    _validate_identifier(schema, "schema")
    _validate_identifier(table, "table")
    return schema, table


def _normalize_table_names(table_names: Union[str, Sequence[str]]) -> Sequence[str]:
    if isinstance(table_names, str):
        return [table_names]
    if isinstance(table_names, (list, tuple)):
        return [t for t in table_names if t]
    raise ValueError("table_names must be a table name string or a list/tuple of table names")


@dataclass(frozen=True)
class HousekeepingConfig:
    retention_months: int = 6
    time_column: str = "data_time"
    time_cast: str = "::timestamptz"
    default_schema: str = "public"
    ignore_missing_table: bool = True
    tmp_suffix: str = "_new"
    vacuum_analyze: bool = True
    create_index: bool = True
    index_columns: Optional[Sequence[Sequence[str]]] = None
    preserve_existing_indexes: bool = True


class PostgresHousekeeper:
    def __init__(self, config: HousekeepingConfig):
        self._config = config
        _validate_identifier(self._config.time_column, "time_column")
        _validate_identifier(self._config.default_schema, "default_schema")

        if not isinstance(self._config.retention_months, int) or self._config.retention_months <= 0:
            raise ValueError("retention_months must be a positive integer")

    def cleanup_table(self, engine, table_name: str) -> int:
        """Keep only last N months by swapping table.

        Strategy (as requested):
          1) CREATE TABLE <table>_new AS SELECT ... WHERE data_time >= now() - interval 'N months'
          2) (optional) create indexes
          3) DROP TABLE <table>
          4) ALTER TABLE <table>_new RENAME TO <table>

        Notes:
          - This approach does NOT preserve constraints/defaults/comments from the original table.
          - If you need to preserve schema details, consider switching to `CREATE TABLE ... (LIKE ... INCLUDING ALL)`.
        """

        schema, table = _parse_table_name(table_name, default_schema=self._config.default_schema)
        tmp_suffix = self._config.tmp_suffix
        if not isinstance(tmp_suffix, str) or not tmp_suffix:
            raise ValueError("tmp_suffix must be a non-empty string")
        if not tmp_suffix.startswith("_"):
            tmp_suffix = f"_{tmp_suffix}"
        # we validate the final tmp table name below

        qualified_table = f'"{schema}"."{table}"'
        new_table_name = f"{table}{tmp_suffix}"
        _validate_identifier(new_table_name, "tmp_table")
        qualified_new_table = f'"{schema}"."{new_table_name}"'

        quoted_col = f'"{self._config.time_column}"'
        time_expr = f"{quoted_col}{self._config.time_cast or ''}"

        months = int(self._config.retention_months)
        interval_literal = f"{months} months"

        index_columns = self._config.index_columns
        if index_columns is None:
            index_columns = [[self._config.time_column]]

        for cols in index_columns:
            for c in cols:
                _validate_identifier(c, "index_column")

        def _index_name(cols: Sequence[str]) -> str:
            base = f"idx_{table}_{'_'.join(cols)}"
            return base[:60]

        def _fetch_existing_indexes(conn) -> List[Tuple[str, str]]:
            rows = conn.execute(
                sa_text(
                    """
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = :schema
                      AND tablename = :table
                    ORDER BY indexname
                    """
                ),
                {"schema": schema, "table": table},
            ).fetchall()
            return [(str(r[0]), str(r[1])) for r in rows]

        def _index_exists(conn, index_name: str) -> bool:
            row = conn.execute(
                sa_text(
                    """
                    SELECT 1
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relkind = 'i'
                      AND n.nspname = :schema
                      AND c.relname = :index
                    LIMIT 1
                    """
                ),
                {"schema": schema, "index": index_name},
            ).fetchone()
            return row is not None

        with engine.begin() as conn:
            try:
                existing_indexes: List[Tuple[str, str]] = []
                if self._config.create_index and self._config.preserve_existing_indexes:
                    existing_indexes = _fetch_existing_indexes(conn)

                conn.execute(sa_text(f"LOCK TABLE {qualified_table} IN ACCESS EXCLUSIVE MODE"))

                conn.execute(sa_text(f"DROP TABLE IF EXISTS {qualified_new_table}"))
                conn.execute(
                    sa_text(
                        f"""
                        CREATE TABLE {qualified_new_table} AS
                        SELECT * FROM {qualified_table}
                        WHERE {time_expr} >= NOW() - INTERVAL '{interval_literal}'
                        """
                    )
                )

                # Swap
                conn.execute(sa_text(f"DROP TABLE {qualified_table}"))
                conn.execute(sa_text(f"ALTER TABLE {qualified_new_table} RENAME TO \"{table}\""))

                # Rebuild indexes (after swap, so names can be stable)
                created_indexes = 0
                if self._config.create_index:
                    if existing_indexes:
                        # Use original index definitions if the table already had indexes.
                        for idx_name, idx_def in existing_indexes:
                            if _index_exists(conn, idx_name):
                                continue
                            conn.execute(sa_text(idx_def))
                            created_indexes += 1
                    else:
                        # Fallback: no index existed, use configured columns (default: data_time)
                        for cols in index_columns:
                            idx_name = _index_name(cols)
                            _validate_identifier(idx_name, "index")
                            cols_sql = ", ".join([f'\"{c}\"' for c in cols])
                            conn.execute(
                                sa_text(
                                    f"CREATE INDEX IF NOT EXISTS \"{idx_name}\" ON {qualified_table} ({cols_sql})"
                                )
                            )
                            created_indexes += 1

                logger.info(
                    "Housekeeping swapped table %s; kept last %s months; indexes_created=%s",
                    f"{schema}.{table}",
                    months,
                    created_indexes,
                )
                processed = 1
            except ProgrammingError as e:
                msg = str(e).lower()
                if self._config.ignore_missing_table and ("does not exist" in msg or "undefined table" in msg):
                    logger.warning("Housekeeping skipped missing table %s: %s", f"{schema}.{table}", e)
                    return 0
                raise

        if self._config.vacuum_analyze and processed:
            # Postgres VACUUM must run outside a transaction block.
            vacuum_sql = sa_text(f"VACUUM (ANALYZE) {qualified_table}")
            conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
            try:
                conn.execute(vacuum_sql)
                logger.info("Housekeeping VACUUM (ANALYZE) done on %s", f"{schema}.{table}")
            finally:
                conn.close()

        return processed

    def cleanup_tables(self, engine, table_names: Iterable[str]) -> int:
        total = 0
        for name in table_names:
            total += self.cleanup_table(engine, name)
        return total


def _config_from_dag_infos(dag_infos: Optional[dict]) -> HousekeepingConfig:
    if not dag_infos:
        return HousekeepingConfig()

    index_columns = dag_infos.get("housekeeping_index_columns")
    if index_columns is not None:
        if not isinstance(index_columns, list):
            raise ValueError("dag_infos['housekeeping_index_columns'] must be a list like [[col1], [col1, col2]]")
        normalized_cols: List[List[str]] = []
        for item in index_columns:
            if isinstance(item, str):
                normalized_cols.append([item])
            elif isinstance(item, list) and all(isinstance(c, str) for c in item):
                normalized_cols.append(item)
            else:
                raise ValueError("Each housekeeping_index_columns item must be a string or list[str]")
        index_columns = normalized_cols

    return HousekeepingConfig(
        retention_months=int(dag_infos.get("housekeeping_retention_months", 6)),
        time_column=str(dag_infos.get("housekeeping_time_column", "data_time")),
        time_cast=str(dag_infos.get("housekeeping_time_cast", "::timestamptz")),
        default_schema=str(dag_infos.get("housekeeping_default_schema", "public")),
        ignore_missing_table=bool(dag_infos.get("housekeeping_ignore_missing_table", True)),
        tmp_suffix=str(dag_infos.get("housekeeping_tmp_suffix", "_new")),
        create_index=bool(dag_infos.get("housekeeping_create_index", True)),
        index_columns=index_columns,
        preserve_existing_indexes=bool(dag_infos.get("housekeeping_preserve_existing_indexes", True)),
        vacuum_analyze=bool(dag_infos.get("housekeeping_vacuum_analyze", True)),
    )


def housekeep_tables(
    table_names: Union[str, Sequence[str]],
    **kwargs,
) -> int:
    """Airflow-friendly housekeeping entrypoint (swap-table retention).

    Usage inside ETL function:
        from utils.housekeeping import housekeep_tables
        housekeep_tables(history_table, **kwargs)

    Required in kwargs:
        ready_data_db_uri (from CommonDag)

    Optional in kwargs:
        dag_infos: can include:
          - housekeeping_retention_months (default 6)
          - housekeeping_time_column (default 'data_time')
          - housekeeping_default_schema (default 'public')
          - housekeeping_ignore_missing_table (default True)
          - housekeeping_preserve_existing_indexes (default True)
          - housekeeping_vacuum_analyze (default True)

    Returns:
        Total processed tables (rowcount is not computed in swap strategy).
    """

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    if not ready_data_db_uri:
        raise ValueError("Missing ready_data_db_uri in kwargs")

    dag_infos = kwargs.get("dag_infos")
    config = _config_from_dag_infos(dag_infos)

    engine = create_engine(ready_data_db_uri)
    housekeeper = PostgresHousekeeper(config)

    normalized = _normalize_table_names(table_names)
    return housekeeper.cleanup_tables(engine, normalized)
