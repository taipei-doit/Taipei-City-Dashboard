"""Stub Airflow modules so existing DE ETL code can run under Windmill.

設計目標：讓現有 `dags/proj_city_dashboard/*/*.py` 的 `_transfer` 函式完全不用改
就能在 Windmill 的 Python script 裡被呼叫。策略是在 import DAG module 之前，把
ETL 程式碼會用到的 `airflow.*` 與 `settings.global_config` 塞進 sys.modules。

這個檔案跟 Kestra PoC 的 shim 幾乎一樣，因為解決的是同一個問題 — 讓非 Airflow
的 runner 能跑原本寫給 Airflow 的程式碼。
"""

import json
import os
import sys
import types


def _build_postgres_hook():
    """Return a PostgresHook-compatible class backed by env-var URIs."""
    from sqlalchemy import create_engine, text

    uri_map = {
        "postgres_default": os.environ["READY_DATA_DB_URI"],
        "dashboad-postgre": os.environ.get(
            "DASHBOARD_DB_URI", os.environ["READY_DATA_DB_URI"]
        ),
    }
    extras = os.environ.get("POSTGRES_CONN_URIS")
    if extras:
        uri_map.update(json.loads(extras))

    class PostgresHook:
        def __init__(self, postgres_conn_id, **_):
            if postgres_conn_id not in uri_map:
                raise KeyError(
                    f"PostgresHook conn '{postgres_conn_id}' 未設定，"
                    f"請在 env 的 POSTGRES_CONN_URIS 補上。現有: {list(uri_map)}"
                )
            self._uri = uri_map[postgres_conn_id]
            self._engine = None

        def _engine_get(self):
            if self._engine is None:
                self._engine = create_engine(self._uri)
            return self._engine

        def get_uri(self):
            return self._uri

        def get_conn(self):
            return self._engine_get().raw_connection()

        def get_sqlalchemy_engine(self):
            return self._engine_get()

        def get_records(self, sql, parameters=None):
            with self._engine_get().connect() as conn:
                stmt = text(sql) if isinstance(sql, str) else sql
                return conn.execute(stmt, parameters or {}).fetchall()

        def get_first(self, sql, parameters=None):
            rows = self.get_records(sql, parameters)
            return rows[0] if rows else None

        def run(self, sql, parameters=None, autocommit=True):
            with self._engine_get().begin() as conn:
                stmt = text(sql) if isinstance(sql, str) else sql
                conn.execute(stmt, parameters or {})

        def get_pandas_df(self, sql, parameters=None):
            import pandas as pd

            stmt = text(sql) if isinstance(sql, str) else sql
            return pd.read_sql(stmt, self._engine_get(), params=parameters)

    return PostgresHook


def _make_module(name):
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


_installed = False


def install():
    """Install all stubs into sys.modules. Idempotent."""
    global _installed
    if _installed:
        return

    if "airflow" not in sys.modules:
        airflow = _make_module("airflow")

        class _DAG:
            def __init__(self, *_, **__):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        airflow.DAG = _DAG

    _make_module("airflow.providers")
    _make_module("airflow.providers.postgres")
    _make_module("airflow.providers.postgres.hooks")
    postgres_hook_mod = _make_module("airflow.providers.postgres.hooks.postgres")
    postgres_hook_mod.PostgresHook = _build_postgres_hook()

    _make_module("airflow.operators")
    empty_mod = _make_module("airflow.operators.empty")
    python_mod = _make_module("airflow.operators.python")

    class _NoopOperator:
        def __init__(self, *_, **__):
            pass

        def __rshift__(self, other):
            return other

        def __lshift__(self, other):
            return other

    empty_mod.EmptyOperator = _NoopOperator
    python_mod.PythonOperator = _NoopOperator

    models_mod = _make_module("airflow.models")

    class Variable:
        @staticmethod
        def get(key, default=None):
            val = os.environ.get(f"AIRFLOW_VAR_{key}")
            if val is not None:
                return val
            return default if default is not None else "[]"

    models_mod.Variable = Variable

    conf_mod = _make_module("airflow.configuration")

    class _Conf:
        @staticmethod
        def get(section, key, fallback=None):
            return os.environ.get(f"AIRFLOW__{section.upper()}__{key.upper()}", fallback)

    conf_mod.conf = _Conf()

    settings_mod = _make_module("settings")
    gc = _make_module("settings.global_config")
    gc.DAG_PATH = os.environ.get("DAG_PATH", "/opt/airflow/dags")
    gc.DATA_PATH = os.environ.get("DATA_PATH", "/opt/airflow/data")
    gc.PROXIES = None
    settings_mod.global_config = gc

    _installed = True
