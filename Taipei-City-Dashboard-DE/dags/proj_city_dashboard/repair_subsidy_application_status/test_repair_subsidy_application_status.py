"""Test for repair_subsidy_application_status DAG.

驗證 data.taipei 來源可達且回傳必要欄位。**不**需要 Airflow / Postgres。

Run from DAG folder:
    python test_repair_subsidy_application_status.py
或從 toolkit:
    python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests


HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "job_config.json").read_text(encoding="utf-8"))
DATA_INFOS = CONFIG["data_infos"]
DAG_INFOS = CONFIG["dag_infos"]
SOURCE_URL = DATA_INFOS["source"]
TABLE_NAME = DAG_INFOS["dag_id"]

TAIPEI_RID = "e54950a4-86b4-407b-bccf-180f17e1b310"


def _fetch_data_taipei(rid: str) -> list[dict]:
    url = f"https://data.taipei/api/v1/dataset/{rid}?scope=resourceAquire&limit=2"
    # data.taipei 憑證缺 Subject Key Identifier,新版 OpenSSL 驗證會失敗;DAG utils 同樣 verify=False
    res = requests.get(url, timeout=30, verify=False)
    res.raise_for_status()
    body = res.json()
    records = (body.get("result") or {}).get("results") or []
    if not records:
        raise AssertionError(f"data.taipei 沒回傳記錄; body keys: {list(body)}")
    return records


def test_source_url_reachable():
    print(f"[{TABLE_NAME}] source={SOURCE_URL}")

    taipei_records = _fetch_data_taipei(TAIPEI_RID)
    taipei_keys = set(taipei_records[0])
    for key in (
        "項目",
        "修繕住宅貸款利息補貼申請戶數",
        "修繕住宅貸款利息補貼計畫戶數",
        "修繕住宅貸款利息補貼核定戶數",
    ):
        if key not in taipei_keys:
            raise AssertionError(f"data.taipei 缺少欄位: {key}")
    print(f"  data.taipei reachable, keys: {list(taipei_records[0].keys())[:12]}")


def test_combined_year_row_values_numeric():
    """合併年度列（如「112-113年度」）的補貼欄位須為數字，拆分邏輯才有依據。"""
    url = f"https://data.taipei/api/v1/dataset/{TAIPEI_RID}?scope=resourceAquire&limit=1000"
    res = requests.get(url, timeout=30, verify=False)
    res.raise_for_status()
    records = (res.json().get("result") or {}).get("results") or []
    combined = [r for r in records if re.match(r"^\d+-\d+年度$", str(r.get("項目", "")))]
    for row in combined:
        for col in (
            "修繕住宅貸款利息補貼申請戶數",
            "修繕住宅貸款利息補貼計畫戶數",
            "修繕住宅貸款利息補貼核定戶數",
        ):
            value = str(row.get(col, "")).replace(",", "").strip()
            if not value.isdigit():
                raise AssertionError(
                    f"合併年度列 {row.get('項目')} 欄位非數字: {col}={row.get(col)}"
                )
    print(f"  combined-year rows: {len(combined)}, values numeric")


if __name__ == "__main__":
    try:
        test_source_url_reachable()
        test_combined_year_row_values_numeric()
    except Exception as e:
        print(f"FAIL [{TABLE_NAME}]: {e}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
