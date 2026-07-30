"""Test for school_food_supply_chain_links DAG.

驗證 data_infos.source 可達。**不**需要 Airflow / Postgres。

⚠️ 注意：fatraceschool API 為 POST + JSON body，需 accesscode 認證。
本機 source URL 測試僅做基礎連線檢查（HEAD/GET 確認 endpoint 存在），
完整 E2E 資料抓取需 Airflow Variable `fatraceschool_accesscode`。

Run from DAG folder:
    python test_school_food_supply_chain_links.py
或從 toolkit:
    python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests
import urllib3

# Windows cp950 stdout 無法輸出 emoji；強制 utf-8 以利本機 print。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# fatraceschool / 部分 .gov.tw 憑證鏈缺 Subject Key Identifier，
# 新版 Python ssl 嚴格驗證會擋。URL 本身可達。Airflow 容器內若無此問題可改回 True。
_VERIFY_SSL = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "job_config.json").read_text(encoding="utf-8"))
DATA_INFOS = CONFIG["data_infos"]
DAG_INFOS = CONFIG["dag_infos"]
SOURCE_URL = DATA_INFOS["source"]
SOURCE_TYPE = DATA_INFOS["source_type"]
TABLE_NAME = DAG_INFOS["dag_id"]


def test_source_url_reachable():
    """fatraceschool OpenAPI base endpoint 可達性檢查。

    本端點為 POST API，無 accesscode 直接 GET 通常會回 405 / 401 / 4xx；
    任何 2xx/3xx/4xx 都代表服務存在；只有 timeout / 5xx / connection refused 才算失敗。
    """
    print(f"[{TABLE_NAME}] source_type={SOURCE_TYPE}")
    print(f"  URL: {SOURCE_URL}")

    try:
        # HEAD 較輕量；服務不支援會 fallback GET
        res = requests.head(
            SOURCE_URL, timeout=30, allow_redirects=True, verify=_VERIFY_SSL
        )
        if res.status_code >= 500:
            res = requests.get(
                SOURCE_URL, timeout=30, allow_redirects=True, verify=_VERIFY_SSL
            )
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"endpoint 無法連線: {e}")

    # 4xx 對 POST-only endpoint 做 GET 是預期行為（如 405 Method Not Allowed）
    # 視為 endpoint 存在；5xx 才當作真正失敗
    if res.status_code >= 500:
        res.raise_for_status()

    print(f"  ✅ endpoint reachable, status={res.status_code}")
    print("     注意：完整資料抓取需 Airflow Variable `fatraceschool_accesscode`")


if __name__ == "__main__":
    try:
        test_source_url_reachable()
    except Exception as e:
        print(f"❌ FAIL [{TABLE_NAME}]: {e}", file=sys.stderr)
        sys.exit(1)
    print("All tests passed")
