"""Test for weather_station_hourly_obs DAG.

驗證 data_infos.source 可達且回傳合理資料。**不**需要 Airflow / Postgres。

source_type=cwa-api:CWA opendata API 需 Authorization 金鑰。
執行測試前請設定環境變數(此值正式執行時由 Airflow Variable CWA_API_KEY 提供):
    export CWA_API_KEY=<你的 CWA 金鑰>

Run from DAG folder:
    python test_weather_station_hourly_obs.py
或從 toolkit:
    python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py
"""
from __future__ import annotations

import json
import os
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

# === 視 source_type 填 ===
# data.taipei: 把 dataset detail 頁面對應的 resource id 填進來(必填)
RID = ""
# csv / csv-big5 編碼:utf-8 / big5 / cp950
ENCODING = "utf-8"
# cwa-api: CWA opendata resource id;金鑰由環境變數 CWA_API_KEY 提供(不可硬編)
CWA_RESOURCE_ID = "O-A0001-001"
CWA_API_KEY_ENV = "CWA_API_KEY"


def _fetch_data_taipei(rid: str) -> list[dict]:
    if not rid:
        raise AssertionError(
            "source_type=data.taipei 但 RID 未填,請於 test 頂端 RID 變數填入 dataset 的 resource id"
        )
    url = f"https://data.taipei/api/dataset/{rid}?scope=resourceAquire&limit=2"
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    body = res.json()
    records = (body.get("result") or {}).get("records") \
              or (body.get("payload") or {}).get("records")
    if not records:
        raise AssertionError(f"data.taipei 沒回傳記錄;body keys: {list(body)}")
    return records


def _fetch_csv(url: str, encoding: str):
    import pandas as pd
    res = requests.get(url, timeout=60)
    res.raise_for_status()
    text = res.content.decode(encoding, errors="replace")
    df = pd.read_csv(StringIO(text))
    if df.empty:
        raise AssertionError("CSV is empty")
    if len(df.columns) == 0:
        raise AssertionError("CSV has no columns")
    return df


def _fetch_binary(url: str) -> int:
    """SHP / ZIP / KML 等二進位:HEAD 看 size,失敗就 streaming GET 一段。"""
    head = requests.head(url, timeout=30, allow_redirects=True)
    head.raise_for_status()
    size = int(head.headers.get("Content-Length", "0"))
    if size > 0:
        return size
    # fallback
    res = requests.get(url, timeout=60, stream=True)
    res.raise_for_status()
    chunk = next(res.iter_content(chunk_size=4096), b"")
    if not chunk:
        raise AssertionError("Source 回應為空")
    return -1   # unknown size 但有資料


def _fetch_json(url: str) -> Any:
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    body = res.json()
    if not body:
        raise AssertionError("JSON response is empty")
    return body


def _fetch_data_ntpc(url: str) -> list[dict]:
    body = _fetch_json(url)
    records = body.get("result", {}).get("records") if isinstance(body, dict) else None
    if not records:
        raise AssertionError(f"data.ntpc 沒回傳記錄;body: {str(body)[:200]}")
    return records


def _fetch_cwa(resource_id: str) -> list[dict]:
    """CWA opendata REST API:金鑰由環境變數讀取,不可硬編。"""
    api_key = os.environ.get(CWA_API_KEY_ENV)
    if not api_key:
        raise AssertionError(
            f"source_type=cwa-api 需要 CWA 金鑰,請先設定環境變數 {CWA_API_KEY_ENV}"
            f"(export {CWA_API_KEY_ENV}=<金鑰>)。正式執行時由 Airflow Variable {CWA_API_KEY_ENV} 提供。"
        )
    url = (
        f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/{resource_id}"
        f"?Authorization={api_key}&format=JSON"
    )
    try:
        res = requests.get(url, timeout=60)
    except requests.exceptions.SSLError:
        # CWA 伺服器憑證在較新版 OpenSSL 下會驗證失敗(Missing Subject Key
        # Identifier,政府網站常見的舊憑證瑕疵)。資料源本身可達,Airflow
        # 容器環境亦不受影響,故此處停用 TLS 驗證重試以完成可達性測試。
        print("  ⚠️ CWA 憑證在本機 OpenSSL 驗證失敗,改用 verify=False 重試(僅本測試)")
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )
        res = requests.get(url, timeout=60, verify=False)
    res.raise_for_status()
    body = res.json()
    stations = (body.get("records") or {}).get("Station")
    if not stations:
        raise AssertionError(f"CWA 沒回傳測站資料;body keys: {list(body)}")
    return stations


def test_source_url_reachable():
    """資料源 URL 可達且回傳合理資料(必過)。"""
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

    elif SOURCE_TYPE == "cwa-api":
        stations = _fetch_cwa(CWA_RESOURCE_ID)
        print(f"  ✅ CWA API reachable, {len(stations)} stations")
        print(f"     keys: {list(stations[0].keys())[:10]}")

    else:
        # fallback:單純 GET 確認 200 + 非空
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
