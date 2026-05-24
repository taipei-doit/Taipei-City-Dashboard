"""Test for river_channel DAG.

驗證 data_infos.source 可達且回傳合理資料。**不**需要 Airflow / Postgres。

Run from DAG folder:
    python test_river_channel.py
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

# === 視 source_type 填 ===
# data.taipei: 把 dataset detail 頁面對應的 resource id 填進來(必填)
RID = ""
# csv / csv-big5 編碼:utf-8 / big5 / cp950
ENCODING = "utf-8"


def _fetch_data_taipei(rid: str) -> list[dict]:
    if not rid:
        raise AssertionError(
            "source_type=data.taipei 但 RID 未填,請於 test 頂端 RID 變數填入 dataset 的 resource id"
        )
    url = f"https://data.taipei/api/dataset/{rid}?scope=resourceAquire&limit=2"
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    body = res.json()
    records = (body.get("result") or {}).get("records") \
              or (body.get("payload") or {}).get("records")
    if not records:
        raise AssertionError(f"data.taipei 沒回傳記錄;body keys: {list(body)}")
    return records


def _fetch_csv(url: str, encoding: str):
    import pandas as pd
    res = requests.get(url, timeout=60)
    res.raise_for_status()
    text = res.content.decode(encoding, errors="replace")
    df = pd.read_csv(StringIO(text))
    if df.empty:
        raise AssertionError("CSV is empty")
    if len(df.columns) == 0:
        raise AssertionError("CSV has no columns")
    return df


def _fetch_binary(url: str, *, verify: bool = True) -> int:
    """SHP / ZIP / KML 等二進位:HEAD 看 size,失敗就 streaming GET 一段。"""
    head = requests.head(url, timeout=30, allow_redirects=True, verify=verify)
    head.raise_for_status()
    size = int(head.headers.get("Content-Length", "0"))
    if size > 0:
        return size
    # fallback
    res = requests.get(url, timeout=60, stream=True, verify=verify)
    res.raise_for_status()
    chunk = next(res.iter_content(chunk_size=4096), b"")
    if not chunk:
        raise AssertionError("Source 回應為空")
    return -1   # unknown size 但有資料


def test_dag_uses_shp_helper_with_required_args():
    """DAG must pass dag_id/from_crs and disable SSL verification for WRA."""
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


def _fetch_json(url: str) -> Any:
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    body = res.json()
    if not body:
        raise AssertionError("JSON response is empty")
    return body


def _fetch_data_ntpc(url: str) -> list[dict]:
    body = _fetch_json(url)
    records = body.get("result", {}).get("records") if isinstance(body, dict) else None
    if not records:
        raise AssertionError(f"data.ntpc 沒回傳記錄;body: {str(body)[:200]}")
    return records


def test_source_url_reachable():
    """資料源 URL 可達且回傳合理資料。"""
    print(f"[{TABLE_NAME}] source_type={SOURCE_TYPE}")

    if SOURCE_TYPE == "data.taipei":
        records = _fetch_data_taipei(RID)
        print(f"  ✅ data.taipei reachable, {len(records)} sample records")
        print(f"     keys: {list(records[0].keys())[:10]}")

    elif SOURCE_TYPE in ("csv", "csv-big5"):
        enc = "big5" if SOURCE_TYPE == "csv-big5" else ENCODING
        df = _fetch_csv(SOURCE_URL, encoding=enc)
        print(f"  ✅ CSV reachable, {len(df)} rows × {len(df.columns)} cols")
        print(f"     columns: {list(df.columns)[:10]}")

    elif SOURCE_TYPE in ("shp", "geojson", "kml", "zip"):
        size = _fetch_binary(SOURCE_URL, verify=False)
        print(f"  ✅ {SOURCE_TYPE.upper()} reachable, Content-Length: {'unknown' if size < 0 else f'{size:,} bytes'}")

    elif SOURCE_TYPE in ("api", "json"):
        body = _fetch_json(SOURCE_URL)
        keys = list(body)[:10] if isinstance(body, dict) else f"list[{len(body)}]"
        print(f"  ✅ JSON API reachable, top-level: {keys}")

    elif SOURCE_TYPE == "data.ntpc":
        records = _fetch_data_ntpc(SOURCE_URL)
        print(f"  ✅ data.ntpc reachable, {len(records)} sample records")

    else:
        # fallback:單純 GET 確認 200 + 非空
        res = requests.get(SOURCE_URL, timeout=30)
        res.raise_for_status()
        if not res.content:
            raise AssertionError(f"source_type={SOURCE_TYPE} 回應為空")
        print(f"  ✅ {SOURCE_TYPE} reachable (fallback), bytes: {len(res.content):,}")


if __name__ == "__main__":
    try:
        test_dag_uses_shp_helper_with_required_args()
        test_source_url_reachable()
    except Exception as e:
        print(f"❌ FAIL [{TABLE_NAME}]: {e}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
