"""Test for food_factory_locations_taipei DAG.

驗證 data_infos.source 可達且回傳合理資料。**不**需要 Airflow / Postgres。

Run from DAG folder:
    python test_food_factory_locations_taipei.py
或從 toolkit:
    python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py
"""
from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from typing import Any

import requests
import urllib3

# Windows cp950 stdout 無法輸出 emoji；強制 utf-8 以利本機 print。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# data.taipei / data.ntpc.gov.tw 部分憑證鏈缺 Subject Key Identifier，
# 新版 Python ssl 嚴格驗證會擋。URL 本身可達（curl 200），純為本機驗證便利
# 跳過 cert chain 驗證；不影響資料正確性。Airflow 容器內若無此問題可改回 True。
_VERIFY_SSL = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "job_config.json").read_text(encoding="utf-8"))
DATA_INFOS = CONFIG["data_infos"]
DAG_INFOS = CONFIG["dag_infos"]
SOURCE_URL = DATA_INFOS["source"]
SOURCE_TYPE = DATA_INFOS["source_type"]
TABLE_NAME = DAG_INFOS["dag_id"]

# === 視 source_type 填 ===
# data.taipei: 把 dataset detail 頁面對應的 resource id 填進來（必填）
RID = ""   # 此 DAG 非 data.taipei API，不需 RID
# csv / csv-big5 編碼：utf-8 / big5 / cp950
ENCODING = "utf-8"


def _fetch_data_taipei(rid: str) -> list[dict]:
    if not rid:
        raise AssertionError(
            "source_type=data.taipei 但 RID 未填，請於 test 頂端 RID 變數填入 dataset 的 resource id"
        )
    url = f"https://data.taipei/api/dataset/{rid}?scope=resourceAquire&limit=2"
    res = requests.get(url, timeout=30, verify=_VERIFY_SSL)
    res.raise_for_status()
    body = res.json()
    records = (body.get("result") or {}).get("records") \
              or (body.get("payload") or {}).get("records")
    if not records:
        raise AssertionError(f"data.taipei 沒回傳記錄；body keys: {list(body)}")
    return records


def _fetch_csv(url: str, encoding: str):
    import pandas as pd
    res = requests.get(url, timeout=60, verify=_VERIFY_SSL)
    res.raise_for_status()
    text = res.content.decode(encoding, errors="replace")
    df = pd.read_csv(StringIO(text))
    if df.empty:
        raise AssertionError("CSV is empty")
    if len(df.columns) == 0:
        raise AssertionError("CSV has no columns")
    return df


def _fetch_binary(url: str) -> int:
    head = requests.head(url, timeout=30, allow_redirects=True, verify=_VERIFY_SSL)
    head.raise_for_status()
    size = int(head.headers.get("Content-Length", "0"))
    if size > 0:
        return size
    res = requests.get(url, timeout=60, stream=True, verify=_VERIFY_SSL)
    res.raise_for_status()
    chunk = next(res.iter_content(chunk_size=4096), b"")
    if not chunk:
        raise AssertionError("Source 回應為空")
    return -1


def _fetch_json(url: str) -> Any:
    res = requests.get(url, timeout=30, verify=_VERIFY_SSL)
    res.raise_for_status()
    body = res.json()
    if not body:
        raise AssertionError("JSON response is empty")
    return body


def _fetch_data_ntpc(url: str) -> list[dict]:
    body = _fetch_json(url)
    records = body.get("result", {}).get("records") if isinstance(body, dict) else None
    if not records:
        raise AssertionError(f"data.ntpc 沒回傳記錄；body: {str(body)[:200]}")
    return records


def test_source_url_reachable():
    """資料源 URL 可達且回傳合理資料（必過）。"""
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
        records = _fetch_data_ntpc(SOURCE_URL)
        print(f"  ✅ data.ntpc reachable, {len(records)} sample records")

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
