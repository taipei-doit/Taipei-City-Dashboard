"""Source test for the Taipei noise monitoring station DAG."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests


HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "job_config.json").read_text(encoding="utf-8"))
SOURCE_TYPE = CONFIG["data_infos"]["source_type"]
TABLE_NAME = CONFIG["dag_infos"]["dag_id"]
PAGE_ID = "e2f4ebf5-bffa-40af-8056-383893721731"


def test_source_url_reachable():
    meta_res = requests.get(
        f"https://data.taipei/api/frontstage/tpeod/dataset.view?id={PAGE_ID}",
        timeout=30,
        verify=False,
    )
    meta_res.raise_for_status()
    resources = meta_res.json().get("payload", {}).get("resources", [])
    if not resources:
        raise AssertionError("data.taipei metadata returned no resources")

    rid = resources[0]["rid"]
    data_res = requests.get(
        f"https://data.taipei/api/v1/dataset/{rid}?scope=resourceAquire&limit=2",
        timeout=30,
        verify=False,
    )
    data_res.raise_for_status()
    records = data_res.json().get("result", {}).get("results", [])
    if not records:
        raise AssertionError("data.taipei noise station resource returned no records")

    print(f"[{TABLE_NAME}] source_type={SOURCE_TYPE}, sample_records={len(records)}")
    print(f"keys: {list(records[0].keys())[:10]}")


if __name__ == "__main__":
    try:
        test_source_url_reachable()
    except Exception as exc:
        print(f"FAIL [{TABLE_NAME}]: {exc}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
