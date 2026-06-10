"""Test for eco_friendly_restaurant_ntpe DAG.

驗證 data_infos.source 可達且回傳合理資料。**不**需要 Airflow / Postgres。

Run from DAG folder:
    python test_eco_friendly_restaurant_ntpe.py
或從 toolkit:
    python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py

Note: data.ntpc 的 SOURCE_URL 是 dataset 頁面(人類友善),test 內用 NTPC_RID 拼裝
      API URL (/api/datasets/<rid>/json),且頂層直接為 list 不是 result.records,
      故就地修 PROMPT.md 模板的 _fetch_data_ntpc(可考慮回頭修 PROMPT.md 統一)。
"""
from __future__ import annotations

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
# data.taipei: dataset detail 頁面對應的 resource id
RID = ""
# data.ntpc: dataset 的 resource id (URL 路徑最後一段 UUID)
NTPC_RID = "e90d14f8-5995-4ebb-af19-8f8fd7d396c8"
# csv / csv-big5 編碼:utf-8 / big5 / cp950
ENCODING = "utf-8"


def _fetch_data_taipei(rid: str) -> list[dict]:
    if not rid:
        raise AssertionError(
            "source_type=data.taipei 但 RID 未填,請於 test 頂端 RID 變數填入 dataset 的 resource id"
        )
    url = f"https://data.taipei/api/v1/dataset/{rid}?scope=resourceAquire&limit=2"
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    body = res.json()
    records = (
        (body.get("result") or {}).get("results")
        or (body.get("result") or {}).get("records")
        or (body.get("payload") or {}).get("records")
    )
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


def _fetch_binary(url: str) -> int:
    head = requests.head(url, timeout=30, allow_redirects=True)
    head.raise_for_status()
    size = int(head.headers.get("Content-Length", "0"))
    if size > 0:
        return size
    res = requests.get(url, timeout=60, stream=True)
    res.raise_for_status()
    chunk = next(res.iter_content(chunk_size=4096), b"")
    if not chunk:
        raise AssertionError("Source 回應為空")
    return -1


def _fetch_json(url: str) -> Any:
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    body = res.json()
    if not body:
        raise AssertionError("JSON response is empty")
    return body


def _fetch_data_ntpc(rid: str) -> list[dict]:
    if not rid:
        raise AssertionError(
            "source_type=data.ntpc 但 NTPC_RID 未填,請於 test 頂端填入 dataset rid"
        )
    url = f"https://data.ntpc.gov.tw/api/datasets/{rid}/json?page=0&size=2"
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    body = res.json()
    # data.ntpc 頂層直接是 list;少數 dataset 仍走 result.records
    if isinstance(body, list):
        records = body
    elif isinstance(body, dict):
        records = body.get("result", {}).get("records") or []
    else:
        records = []
    if not records:
        raise AssertionError(f"data.ntpc 沒回傳記錄;body type={type(body).__name__}")
    return records


def test_source_url_reachable():
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
        size = _fetch_binary(SOURCE_URL)
        print(f"  ✅ {SOURCE_TYPE.upper()} reachable, Content-Length: {'unknown' if size < 0 else f'{size:,} bytes'}")

    elif SOURCE_TYPE in ("api", "json"):
        body = _fetch_json(SOURCE_URL)
        keys = list(body)[:10] if isinstance(body, dict) else f"list[{len(body)}]"
        print(f"  ✅ JSON API reachable, top-level: {keys}")

    elif SOURCE_TYPE == "data.ntpc":
        records = _fetch_data_ntpc(NTPC_RID)
        print(f"  ✅ data.ntpc reachable, {len(records)} sample records")
        print(f"     keys: {list(records[0].keys())[:10]}")

    else:
        res = requests.get(SOURCE_URL, timeout=30)
        res.raise_for_status()
        if not res.content:
            raise AssertionError(f"source_type={SOURCE_TYPE} 回應為空")
        print(f"  ✅ {SOURCE_TYPE} reachable (fallback), bytes: {len(res.content):,}")


if __name__ == "__main__":
    try:
        test_source_url_reachable()
    except Exception as e:
        print(f"❌ FAIL [{TABLE_NAME}]: {e}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
