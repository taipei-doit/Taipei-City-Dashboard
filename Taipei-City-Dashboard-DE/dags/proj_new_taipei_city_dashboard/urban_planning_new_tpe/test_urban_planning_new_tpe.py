"""Test for urban_planning_new_tpe DAG.

驗證 data_infos.source 與 ETL 會下載的 SHP / 行政區界線來源可達。**不**需要 Airflow / Postgres。

Run from DAG folder:
    python test_urban_planning_new_tpe.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "job_config.json").read_text(encoding="utf-8"))
DATA_INFOS = CONFIG["data_infos"]
DAG_INFOS = CONFIG["dag_infos"]
SOURCE_URL = DATA_INFOS["source"]
SOURCE_TYPE = DATA_INFOS["source_type"]
TABLE_NAME = DAG_INFOS["dag_id"]

DATASET_ID = "fe26e0a5-54c2-4876-bbc7-150243c048f5"
TAIPEI_PAGE_ID = "3bab0a01-7936-4218-8cb5-f74dfcb43dda"
TAIPEI_FALLBACK_RID = "10196e7d-2460-4b8a-b1d2-84001d09d7a4"
DISTRICT_URL = (
    "https://www.tgos.tw/tgos/VirtualDir/Product/"
    "3fe61d4a-ca23-4f45-8aca-4a536f40f290/"
    "%E9%84%89%28%E9%8E%AE%E3%80%81%E5%B8%82%E3%80%81%E5%8D%80%29"
    "%E7%95%8C%E7%B7%9A1140318.zip"
)


def _head_or_probe(url: str, verify: bool = True) -> int:
    res = requests.head(url, timeout=30, allow_redirects=True, verify=verify)
    if res.status_code == 405:
        res = requests.get(url, timeout=30, stream=True, verify=verify)
    res.raise_for_status()
    size = int(res.headers.get("Content-Length", "0"))
    if size <= 0 and getattr(res, "raw", None):
        chunk = next(res.iter_content(chunk_size=4096), b"")
        if not chunk:
            raise AssertionError(f"Source 回應為空: {url}")
        return -1
    return size


def test_source_url_reachable():
    print(f"[{TABLE_NAME}] source_type={SOURCE_TYPE}")

    page = requests.get(SOURCE_URL, timeout=30, verify=False)
    page.raise_for_status()
    print("  data.ntpc dataset page reachable")

    api_url = f"https://data.ntpc.gov.tw/api/datasets/{DATASET_ID}/json"
    res = requests.get(api_url, params={"page": 0, "size": 3}, timeout=30, verify=False)
    res.raise_for_status()
    records = res.json()
    if not records:
        raise AssertionError("data.ntpc API returned no records")
    zone_url = next(
        row["link"] for row in records if "使用分區" in row.get("name", "")
    )
    print(f"  data.ntpc API reachable, {len(records)} records")

    shp_size = _head_or_probe(zone_url, verify=False)
    print(f"  New Taipei SHP reachable, Content-Length: {'unknown' if shp_size < 0 else shp_size}")

    taipei_source = (
        "https://data.taipei/dataset/detail"
        f"?id={TAIPEI_PAGE_ID}"
    )
    taipei_page = requests.get(taipei_source, timeout=30, verify=False)
    taipei_page.raise_for_status()
    if TAIPEI_PAGE_ID not in taipei_page.text:
        raise AssertionError("data.taipei dataset page did not contain expected page id")
    taipei_shp_url = (
        "https://data.taipei/api/frontstage/tpeod/dataset/resource.download"
        f"?rid={TAIPEI_FALLBACK_RID}"
    )
    taipei_shp_size = _head_or_probe(taipei_shp_url, verify=False)
    print(
        "  Taipei SHP reachable, "
        f"Content-Length: {'unknown' if taipei_shp_size < 0 else taipei_shp_size}"
    )

    district_size = _head_or_probe(DISTRICT_URL, verify=False)
    print(
        "  district boundary SHP reachable, "
        f"Content-Length: {'unknown' if district_size < 0 else district_size}"
    )


if __name__ == "__main__":
    try:
        test_source_url_reachable()
    except Exception as e:
        print(f"FAIL [{TABLE_NAME}]: {e}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
