"""Test for river_channel_ntpe DAG.

驗證 data_infos.source 可達且回傳合理資料。**不**需要 Airflow / Postgres。
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

# constants
RID = ""
ENCODING = "utf-8"

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


def test_source_url_reachable():
    print(f"[{TABLE_NAME}] source_type={SOURCE_TYPE}")
    if SOURCE_TYPE in ("shp", "geojson", "kml", "zip"):
        size = _fetch_binary(SOURCE_URL)
        print(f"  ✅ {SOURCE_TYPE.upper()} reachable, Content-Length: {'unknown' if size < 0 else f'{size:,} bytes'}")
    else:
        res = requests.get(SOURCE_URL, timeout=30)
        res.raise_for_status()
        if not res.content:
            raise AssertionError("回應為空")
        print(f"  ✅ reachable, bytes: {len(res.content):,}")


if __name__ == "__main__":
    try:
        test_source_url_reachable()
    except Exception as e:
        print(f"❌ FAIL [{TABLE_NAME}]: {e}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
