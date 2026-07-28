"""Source test for the New Taipei noise monitoring station DAG."""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import requests


HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "job_config.json").read_text(encoding="utf-8"))
SOURCE_TYPE = CONFIG["data_infos"]["source_type"]
TABLE_NAME = CONFIG["dag_infos"]["dag_id"]
SOURCE_URL = (
    "https://data.ntpc.gov.tw/api/datasets/"
    "cad88b80-8230-48d4-a8d4-ce478954fddf/json"
)


def test_source_url_reachable():
    response = requests.get(
        SOURCE_URL,
        params={"page": 0, "size": 2},
        timeout=30,
        verify=False,
    )
    response.raise_for_status()
    body = response.json()
    records = body.get("value", []) if isinstance(body, dict) else body
    if not records:
        raise AssertionError("data.ntpc noise station endpoint returned no records")

    print(f"[{TABLE_NAME}] source_type={SOURCE_TYPE}, sample_records={len(records)}")
    print(f"keys: {list(records[0].keys())[:10]}")


def test_dag_uses_shared_ntpc_client():
    dag_path = HERE / f"{TABLE_NAME}.py"
    tree = ast.parse(dag_path.read_text(encoding="utf-8"))

    imports_requests = any(
        isinstance(node, ast.Import)
        and any(alias.name == "requests" for alias in node.names)
        for node in ast.walk(tree)
    )
    calls_requests_get = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "requests"
        for node in ast.walk(tree)
    )
    if imports_requests or calls_requests_get:
        raise AssertionError("DAG should use shared NewTaipeiAPIClient instead of inline requests")


if __name__ == "__main__":
    try:
        test_source_url_reachable()
        test_dag_uses_shared_ntpc_client()
    except Exception as exc:
        print(f"FAIL [{TABLE_NAME}]: {exc}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
