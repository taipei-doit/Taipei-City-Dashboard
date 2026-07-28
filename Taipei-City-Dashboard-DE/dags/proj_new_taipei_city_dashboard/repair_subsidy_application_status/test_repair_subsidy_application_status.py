"""Test for repair_subsidy_application_status DAG.

驗證 data.ntpc 來源可達且回傳必要欄位。**不**需要 Airflow / Postgres。

Run from DAG folder:
    python test_repair_subsidy_application_status.py
或從 toolkit:
    python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests


HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "job_config.json").read_text(encoding="utf-8"))
DATA_INFOS = CONFIG["data_infos"]
DAG_INFOS = CONFIG["dag_infos"]
SOURCE_URL = DATA_INFOS["source"]
TABLE_NAME = DAG_INFOS["dag_id"]

NTPC_RID = "502d1589-3693-4f2c-9c05-22e3ec37330d"


def _fetch_data_ntpc(rid: str) -> list[dict]:
    url = f"https://data.ntpc.gov.tw/api/datasets/{rid}/json?page=0&size=2"
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    records = res.json()
    if not records:
        raise AssertionError("data.ntpc 沒回傳記錄")
    return records


def test_source_url_reachable():
    print(f"[{TABLE_NAME}] source={SOURCE_URL}")

    ntpc_records = _fetch_data_ntpc(NTPC_RID)
    ntpc_keys = set(ntpc_records[0])
    for key in (
        "year",
        "repair_apply_num",
        "repair_project_num",
        "repair_ok_num",
    ):
        if key not in ntpc_keys:
            raise AssertionError(f"data.ntpc 缺少欄位: {key}")
    print(f"  data.ntpc reachable, keys: {list(ntpc_records[0].keys())[:12]}")


if __name__ == "__main__":
    try:
        test_source_url_reachable()
    except Exception as e:
        print(f"FAIL [{TABLE_NAME}]: {e}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
