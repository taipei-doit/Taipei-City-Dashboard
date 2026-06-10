"""Test for food_hygiene_award_locations DAG.

驗證兩個 source URL/API 可達且回傳合理資料。**不**需要 Airflow / Postgres。

Run from DAG folder:
    python test_food_hygiene_award_locations.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests
import urllib3


HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "job_config.json").read_text(encoding="utf-8"))
DATA_INFOS = CONFIG["data_infos"]
DAG_INFOS = CONFIG["dag_infos"]
SOURCE_URL = DATA_INFOS["source"]
SOURCE_TYPE = DATA_INFOS["source_type"]
TABLE_NAME = DAG_INFOS["dag_id"]

TAIPEI_RID = "c5646d80-9118-4439-b924-075f96371d75"
TAIPEI_API_URL = f"https://data.taipei/api/v1/dataset/{TAIPEI_RID}"
NTPC_API_URL = "https://foodtracer.health.ntpc.gov.tw/FoodMap/GetFoodAwardMarkers"
NTPC_DISTRICTS = (
    "萬里區,金山區,板橋區,汐止區,深坑區,石碇區,瑞芳區,平溪區,雙溪區,貢寮區,"
    "新店區,坪林區,烏來區,永和區,中和區,土城區,三峽區,樹林區,鶯歌區,三重區,"
    "新莊區,泰山區,林口區,蘆洲區,五股區,八里區,淡水區,三芝區,石門區"
)


def _fetch_taipei_records() -> list[dict]:
    res = requests.get(
        TAIPEI_API_URL,
        params={"scope": "resourceAquire", "limit": 2},
        timeout=30,
    )
    res.raise_for_status()
    body = res.json()
    records = body.get("result", {}).get("results")
    if not records:
        raise AssertionError(f"臺北 data.taipei 沒回傳記錄; body keys: {list(body)}")
    return records


def _fetch_ntpc_records() -> list[dict]:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    res = requests.post(
        NTPC_API_URL,
        data={"ZoneID": NTPC_DISTRICTS},
        timeout=60,
        verify=False,
    )
    res.raise_for_status()
    records = res.json()
    if not isinstance(records, list) or not records:
        raise AssertionError("新北 FoodTracer API 沒回傳 marker list")
    required_keys = {"label", "Address", "lon", "lat", "Name"}
    missing = required_keys - set(records[0])
    if missing:
        raise AssertionError(f"新北 FoodTracer marker 缺欄位: {sorted(missing)}")
    return records


def test_source_url_reachable():
    print(f"[{TABLE_NAME}] source_type={SOURCE_TYPE}")
    print(f"  source={SOURCE_URL}")

    taipei_records = _fetch_taipei_records()
    print(f"  ✅ 臺北 data.taipei reachable, sample keys: {list(taipei_records[0].keys())}")

    ntpc_records = _fetch_ntpc_records()
    print(f"  ✅ 新北 FoodTracer reachable, sample keys: {list(ntpc_records[0].keys())[:10]}")


if __name__ == "__main__":
    try:
        test_source_url_reachable()
    except Exception as e:
        print(f"❌ FAIL [{TABLE_NAME}]: {e}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
