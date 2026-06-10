"""Test for food_supply_market_locations DAG.

驗證 data_infos.source 相關 URL/API 可達且回傳合理資料。**不**需要 Airflow / Postgres。

Run from DAG folder:
    python test_food_supply_market_locations.py
或從 toolkit:
    python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py
"""
from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

import pandas as pd
import requests


HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "job_config.json").read_text(encoding="utf-8"))
DATA_INFOS = CONFIG["data_infos"]
DAG_INFOS = CONFIG["dag_infos"]
SOURCE_URL = DATA_INFOS["source"]
SOURCE_TYPE = DATA_INFOS["source_type"]
TABLE_NAME = DAG_INFOS["dag_id"]

TAIPEI_STALLS_URL = (
    "https://data.taipei/api/dataset/f490476d-d156-4492-a463-cf3405de3b55"
    "/resource/b0ef64c1-d920-44ba-8bfb-821456ce660b/download"
)
TAIPEI_BASIC_URL = (
    "https://data.taipei/api/dataset/89bebb3a-990d-4070-bd67-631a575f6d4a"
    "/resource/35acfce1-2c4d-4c70-aa75-601cdab2b3f7/download"
)
NTPC_URL = (
    "https://data.ntpc.gov.tw/api/datasets/"
    "785be91a-caaf-4e1c-91d6-f7d616d31a45/json?page=0&size=2"
)


def _fetch_csv(url: str, encoding: str) -> pd.DataFrame:
    res = requests.get(url, timeout=60)
    res.raise_for_status()
    text = res.content.decode(encoding, errors="replace")
    df = pd.read_csv(StringIO(text))
    if df.empty:
        raise AssertionError(f"CSV is empty: {url}")
    return df


def _fetch_json(url: str) -> list[dict]:
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    body = res.json()
    if not isinstance(body, list) or not body:
        raise AssertionError(f"JSON response is empty or not a list: {url}")
    return body


def test_source_url_reachable():
    """資料源 URL 可達且回傳合理資料(必過)。"""
    print(f"[{TABLE_NAME}] source_type={SOURCE_TYPE}")
    print(f"  source={SOURCE_URL}")

    if SOURCE_TYPE == "api":
        stalls = _fetch_csv(TAIPEI_STALLS_URL, encoding="big5")
        required_stalls = {"市場名稱", "總計", "蔬菜（數量）", "飲食（數量）"}
        missing_stalls = required_stalls - set(stalls.columns)
        if missing_stalls:
            raise AssertionError(f"臺北攤位數 CSV 缺欄位: {sorted(missing_stalls)}")
        print(f"  ✅ 臺北攤位數 CSV reachable, rows={len(stalls)}")

        basic = _fetch_csv(TAIPEI_BASIC_URL, encoding="big5")
        required_basic = {"stitle", "xAddress", "GTag_longitude", "GTag_latitude"}
        missing_basic = required_basic - set(basic.columns)
        if missing_basic:
            raise AssertionError(f"臺北市場基本資料 CSV 缺欄位: {sorted(missing_basic)}")
        print(f"  ✅ 臺北市場基本資料 CSV reachable, rows={len(basic)}")

        ntpc = _fetch_json(NTPC_URL)
        required_ntpc = {"name", "town", "address", "types"}
        missing_ntpc = required_ntpc - set(ntpc[0])
        if missing_ntpc:
            raise AssertionError(f"新北市場 API 缺欄位: {sorted(missing_ntpc)}")
        print(f"  ✅ 新北市場 API reachable, sample keys={list(ntpc[0].keys())}")
    else:
        res = requests.get(SOURCE_URL, timeout=30)
        res.raise_for_status()
        if not res.content:
            raise AssertionError(f"source_type={SOURCE_TYPE} 回應為空")
        print(f"  ✅ {SOURCE_TYPE} reachable (fallback), bytes={len(res.content):,}")


if __name__ == "__main__":
    try:
        test_source_url_reachable()
    except Exception as e:
        print(f"❌ FAIL [{TABLE_NAME}]: {e}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
