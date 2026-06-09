"""Test for river_channel_ntpe DAG.

驗證 data_infos.source 可達且回傳合理資料。**不**需要 Airflow / Postgres。
"""
from __future__ import annotations

import ast
import json
import sys
from io import StringIO
from pathlib import Path
from typing import Any

import requests


HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "job_config.json").read_text(encoding="utf-8"))
DATA_INFOS = CONFIG["data_infos"]
DAG_INFOS = CONFIG["dag_infos"]
SOURCE_URL = DATA_INFOS["source"]
SOURCE_TYPE = DATA_INFOS["source_type"]
TABLE_NAME = DAG_INFOS["dag_id"]

# constants
RID = ""
ENCODING = "utf-8"

def _fetch_binary(url: str, *, verify: bool = True) -> int:
    head = requests.head(url, timeout=30, allow_redirects=True, verify=verify)
    head.raise_for_status()
    size = int(head.headers.get("Content-Length", "0"))
    if size > 0:
        return size
    res = requests.get(url, timeout=60, stream=True, verify=verify)
    res.raise_for_status()
    chunk = next(res.iter_content(chunk_size=4096), b"")
    if not chunk:
        raise AssertionError("Source 回應為空")
    return -1


def test_dag_uses_shp_helper_with_required_args():
    tree = ast.parse((HERE / f"{TABLE_NAME}.py").read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "get_shp_file"
    ]
    if len(calls) != 1:
        raise AssertionError(f"Expected exactly one get_shp_file call, found {len(calls)}")

    call = calls[0]
    if len(call.args) < 3:
        raise AssertionError("get_shp_file must be called with url, dag_id, and from_crs")

    is_verify = next((kw.value for kw in call.keywords if kw.arg == "is_verify"), None)
    if not isinstance(is_verify, ast.Constant) or is_verify.value is not False:
        raise AssertionError("WRA SHP source must pass is_verify=False")


def test_source_url_reachable():
    print(f"[{TABLE_NAME}] source_type={SOURCE_TYPE}")
    if SOURCE_TYPE in ("shp", "geojson", "kml", "zip"):
        size = _fetch_binary(SOURCE_URL, verify=False)
        print(f"  ✅ {SOURCE_TYPE.upper()} reachable, Content-Length: {'unknown' if size < 0 else f'{size:,} bytes'}")
    else:
        res = requests.get(SOURCE_URL, timeout=30)
        res.raise_for_status()
        if not res.content:
            raise AssertionError("回應為空")
        print(f"  ✅ reachable, bytes: {len(res.content):,}")


if __name__ == "__main__":
    try:
        test_dag_uses_shp_helper_with_required_args()
        test_source_url_reachable()
    except Exception as e:
        print(f"❌ FAIL [{TABLE_NAME}]: {e}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
