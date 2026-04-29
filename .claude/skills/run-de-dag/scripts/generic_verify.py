"""
Generic post-run verification for any Taipei-City-Dashboard-DE DAG.

Reads job_config.json to discover tables and load_behavior, then runs:
  - default table exists & row count >= 1
  - history table exists & row >= default (if load_behavior == "current+history")
  - wkb_geometry all non-NULL (if is_geometry == 1)
  - dataset_info.lasttime_in_data updated within recent N minutes
  - prints first 3 rows of default table for human inspection

If a DAG-specific verifier exists at verifications/<dag_id>.py, its verify()
function is invoked and its results are appended.

Usage (run inside airflow-scheduler container):
    DAG_ID=mrt_a11y_alert \\
    JOB_CONFIG_PATH=/opt/airflow/dags/proj_city_dashboard/mrt_a11y_alert/job_config.json \\
    python -

  Optionally:
    CUSTOM_VERIFIER_SRC="<contents of verifications/<dag_id>.py>"
    LASTTIME_FRESHNESS_MIN=10  (default: 10 min)

Exit code 0 = all PASS, 1 = at least one FAIL.
"""
import json
import os
import re
import sys
import importlib.util
from datetime import datetime, timezone, timedelta

from airflow.providers.postgres.hooks.postgres import PostgresHook

CONN_ID = "postgres_default"

# 允許的 table name 格式：字母/數字/底線，可含 schema prefix（schema.table）
_TABLE_NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$')


def safe_table(name: str) -> str:
    """驗證 table name 格式，防止 job_config 被竄改時 f-string 查詢遭注入。
    Table name 來自受控的 job_config.json，屬 trusted local input，
    但仍做白名單檢查以防範未來 config 被 supply-chain 汙染。
    """
    if not _TABLE_NAME_RE.match(name):
        print(f"❌ Invalid table name: {name!r}")
        sys.exit(2)
    return name


def load_config():
    path = os.environ.get("JOB_CONFIG_PATH")
    if not path or not os.path.exists(path):
        print(f"❌ JOB_CONFIG_PATH not set or invalid: {path}")
        sys.exit(2)
    with open(path) as f:
        cfg = json.load(f)
    return cfg["dag_infos"], cfg.get("data_infos", {})


def maybe_load_custom_verifier(dag_id):
    """If skill ships a custom verifier for this dag_id, load it dynamically.

    The verifier source is passed via env CUSTOM_VERIFIER_SRC (string of code)
    so we don't need to mount the skill scripts dir into the container.
    """
    src = os.environ.get("CUSTOM_VERIFIER_SRC", "").strip()
    if not src:
        return None
    spec = importlib.util.spec_from_loader(f"custom_{dag_id}", loader=None)
    mod = importlib.util.module_from_spec(spec)
    try:
        exec(compile(src, f"<custom_{dag_id}>", "exec"), mod.__dict__)
    except Exception as e:
        print(f"⚠️ Custom verifier failed to compile: {type(e).__name__}: {e}")
        return None
    return getattr(mod, "verify", None)


def main():
    dag_infos, data_infos = load_config()
    dag_id = dag_infos["dag_id"]
    default_table = safe_table(dag_infos["ready_data_default_table"])
    history_table = dag_infos.get("ready_data_history_table") or ""
    if history_table:
        history_table = safe_table(history_table)
    load_behavior = dag_infos.get("load_behavior", "")
    is_geometry = data_infos.get("is_geometry", 0) == 1

    freshness_min = int(os.environ.get("LASTTIME_FRESHNESS_MIN", "10"))

    hook = PostgresHook(postgres_conn_id=CONN_ID)
    results = []

    def check(name, ok, detail=""):
        results.append((name, ok, detail))
        mark = "✅" if ok else "❌"
        print(f"  {mark} {name}{(': ' + detail) if detail else ''}")

    print(f"== Generic verify: {dag_id} ==")
    print(f"   default_table={default_table}")
    print(f"   history_table={history_table or '(none)'}")
    print(f"   load_behavior={load_behavior}, is_geometry={is_geometry}")

    # 1. default table exists & has rows
    try:
        default_count = hook.get_first(f"SELECT COUNT(*) FROM {default_table}")[0]
    except Exception as e:
        check(
            f"default table {default_table} exists",
            False,
            f"{type(e).__name__}: {e}",
        )
        print("\n❌ FAIL early")
        sys.exit(1)
    check(
        f"default row count >= 1",
        default_count >= 1,
        f"actual={default_count}",
    )

    # 2. history table (only when current+history)
    if load_behavior == "current+history" and history_table:
        try:
            history_count = hook.get_first(f"SELECT COUNT(*) FROM {history_table}")[0]
            check(
                "history row count >= default",
                history_count >= default_count,
                f"history={history_count}, default={default_count}",
            )
        except Exception as e:
            check(
                f"history table {history_table} exists",
                False,
                f"{type(e).__name__}: {e}",
            )

    # 3. geometry non-null
    if is_geometry:
        try:
            null_geom = hook.get_first(
                f"SELECT COUNT(*) FROM {default_table} WHERE wkb_geometry IS NULL"
            )[0]
            check(
                "wkb_geometry all non-null",
                null_geom == 0,
                f"null={null_geom}",
            )
        except Exception as e:
            check("wkb_geometry column accessible", False, str(e))

    # 4. dataset_info.lasttime_in_data freshness
    try:
        row = hook.get_first(
            f"SELECT lasttime_in_data FROM dataset_info WHERE airflow_dag_id = '{dag_id}'"
        )
        if row is None or row[0] is None:
            check(
                f"dataset_info.lasttime_in_data exists",
                False,
                "row not found or NULL",
            )
        else:
            lasttime = row[0]
            now = datetime.now(timezone.utc)
            if lasttime.tzinfo is None:
                lasttime = lasttime.replace(tzinfo=timezone.utc)
            age = now - lasttime
            ok = age <= timedelta(days=400)  # very lenient: just sanity
            recent = age <= timedelta(minutes=freshness_min)
            check(
                "dataset_info.lasttime_in_data is set",
                ok,
                f"value={lasttime.isoformat()}",
            )
            check(
                f"dataset_info.lasttime_in_data updated within {freshness_min} min",
                recent,
                f"age={age}",
            )
    except Exception as e:
        check("dataset_info accessible", False, str(e))

    # 5. preview first 3 rows
    print("\n   First 3 rows preview:")
    try:
        rows = hook.get_records(f"SELECT * FROM {default_table} LIMIT 3")
        for r in rows:
            preview = ", ".join(
                f"{str(v)[:60]}{'…' if len(str(v)) > 60 else ''}" for v in r
            )
            print(f"     • {preview}")
    except Exception as e:
        print(f"     (preview failed: {e})")

    # 6. custom verifier (optional)
    custom_verify = maybe_load_custom_verifier(dag_id)
    if custom_verify:
        print(f"\n== Custom verify: {dag_id} ==")
        try:
            custom_results = custom_verify(hook, dag_infos)
            for name, ok, detail in custom_results:
                check(name, ok, detail)
        except Exception as e:
            check(
                f"custom verifier {dag_id}.verify() ran cleanly",
                False,
                f"{type(e).__name__}: {e}",
            )
    else:
        print(f"\n   (no custom verifier for {dag_id}; generic checks only)")

    # summary
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n{'✅' if passed == total else '❌'} {passed}/{total} passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
