"""Test for organic_farm_locations DAG.

驗證兩個 source URL/API 可達且回傳合理資料。**不**需要 Airflow / Postgres。

Run from DAG folder:
    python test_organic_farm_locations.py
或從 toolkit:
    python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py
"""
from __future__ import annotations

import json
import sys
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

SUPPORTED_SOURCE_TYPE = "data.taipei,data.ntpc"
TAIPEI_PAGE_ID = "32aea2da-14a7-47b6-a687-57e29c1ad4a7"
TAIPEI_RID = "cb8bccd9-81e1-4e20-835e-a04080037f1e"
NTPC_DATASET_ID = "fc30f585-66d9-4233-a65e-c650d177ebfe"


def _fetch_json(url: str, **params: Any) -> Any:
    res = requests.get(url, params=params, timeout=30)
    res.raise_for_status()
    body = res.json()
    if not body:
        raise AssertionError("JSON response is empty")
    return body


def _fetch_data_taipei_metadata() -> dict:
    url = "https://data.taipei/api/frontstage/tpeod/dataset.view"
    body = _fetch_json(url, id=TAIPEI_PAGE_ID)
    payload = body.get("payload") or {}
    resources = payload.get("resources") or []
    if not resources:
        raise AssertionError(f"data.taipei metadata 沒回傳 resources; body keys: {list(body)}")
    if not any(resource.get("rid") == TAIPEI_RID for resource in resources):
        raise AssertionError(f"data.taipei resources 找不到 RID={TAIPEI_RID}")
    return payload


def _fetch_data_taipei_records() -> list[dict]:
    url = f"https://data.taipei/api/v1/dataset/{TAIPEI_RID}"
    body = _fetch_json(url, scope="resourceAquire", limit=2)
    records = (body.get("result") or {}).get("results")
    if not records:
        raise AssertionError(f"data.taipei 沒回傳記錄; body keys: {list(body)}")
    required_keys = {"農場名稱", "農友姓名", "通訊地址", "認證字號", "面積（公頃）"}
    missing = required_keys - set(records[0])
    if missing:
        raise AssertionError(f"data.taipei sample 缺欄位: {sorted(missing)}")
    return records


def _fetch_data_ntpc_records() -> list[dict]:
    url = f"https://data.ntpc.gov.tw/api/datasets/{NTPC_DATASET_ID}/json"
    records = _fetch_json(url, size=2)
    if not isinstance(records, list) or not records:
        raise AssertionError("data.ntpc 沒回傳 record list")
    required_keys = {"operators", "counties", "town", "address", "phone", "produce", "date", "farm", "test"}
    missing = required_keys - set(records[0])
    if missing:
        raise AssertionError(f"data.ntpc sample 缺欄位: {sorted(missing)}")
    return records


def test_source_url_reachable():
    """資料源 URL 可達且回傳合理資料(必過)。"""
    if SOURCE_TYPE != SUPPORTED_SOURCE_TYPE:
        raise AssertionError(f"source_type 應為 {SUPPORTED_SOURCE_TYPE},目前: {SOURCE_TYPE}")

    print(f"[{TABLE_NAME}] source_type={SOURCE_TYPE}")
    print(f"  source={SOURCE_URL}")

    metadata = _fetch_data_taipei_metadata()
    print(f"  ✅ data.taipei metadata reachable, title: {metadata.get('title')}")

    taipei_records = _fetch_data_taipei_records()
    print(f"  ✅ data.taipei records reachable, keys: {list(taipei_records[0].keys())[:10]}")

    ntpc_records = _fetch_data_ntpc_records()
    print(f"  ✅ data.ntpc records reachable, keys: {list(ntpc_records[0].keys())[:10]}")


if __name__ == "__main__":
    try:
        test_source_url_reachable()
    except Exception as e:
        print(f"❌ FAIL [{TABLE_NAME}]: {e}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
