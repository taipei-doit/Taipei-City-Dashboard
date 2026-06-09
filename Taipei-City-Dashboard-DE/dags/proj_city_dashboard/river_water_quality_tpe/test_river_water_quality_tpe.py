"""Source test for the Taipei river water quality DAG.

Run from this DAG folder:
    python test_river_water_quality_tpe.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests


HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "job_config.json").read_text(encoding="utf-8"))
SOURCE_TYPE = CONFIG["data_infos"]["source_type"]
TABLE_NAME = CONFIG["dag_infos"]["dag_id"]
DATASET_CODE = "WQX_P_01"
COUNTY = "臺北市"


def test_source_url_reachable():
    api_key = os.getenv("MOENV_API_KEY")
    if not api_key:
        raise AssertionError("MOENV_API_KEY is required for MOENV source URL test")

    url = f"https://data.moenv.gov.tw/api/v2/{DATASET_CODE}"
    res = requests.get(
        url,
        params={
            "format": "json",
            "limit": 2,
            "offset": 0,
            "api_key": api_key,
            "filters": f"county,EQ,{COUNTY}",
            "sort": "SampleDate desc",
        },
        timeout=30,
        verify=False,
    )
    res.raise_for_status()
    records = res.json()
    if not isinstance(records, list) or not records:
        raise AssertionError("MOENV API returned no river water quality records")

    required = {"siteid", "sitename", "county", "twd97lon", "twd97lat", "sampledate"}
    missing = required - set(records[0])
    if missing:
        raise AssertionError(f"MOENV sample record missing fields: {sorted(missing)}")
    if records[0]["county"] != COUNTY:
        raise AssertionError(f"Expected county={COUNTY}, got {records[0]['county']}")

    print(f"[{TABLE_NAME}] source_type={SOURCE_TYPE}, sample_records={len(records)}")
    print(f"keys: {list(records[0].keys())[:10]}")


if __name__ == "__main__":
    try:
        test_source_url_reachable()
    except Exception as exc:
        print(f"FAIL [{TABLE_NAME}]: {exc}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
