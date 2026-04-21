"""
standalone_etl.py
=================
不依賴 Airflow 的獨立 ETL 腳本，流程對應 template_dag.py。
資料來源：data.taipei / data.ntpc API
輸出：CSV 檔案

使用方式：
  # 執行預設資料集（etl_config.json 的 _default）
  python ETL.py

  # 指定 dag_id
  python ETL.py --dag-id 臺北市文化資產

  （新增資料集請用 gen_config.py；新增 transform 策略請在 transforms/ 新增對應檔案）
"""

import importlib
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import pandas as pd
import json
from datetime import datetime
import os
import argparse

from transform_utils import TAIPEI_TZ, get_source_last_modified, transform_single

_HERE        = os.path.dirname(os.path.abspath(__file__))
_DE_ROOT     = os.path.abspath(os.path.join(_HERE, "..", ".."))
OUTPUT_DIR   = os.path.join(_DE_ROOT, "data")
_CONFIG_PATH = os.path.join(_HERE, "etl_config.json")


def _load_configs() -> tuple[dict, str]:
    """載入 etl_config.json，回傳 (DATASET_CONFIGS, DEFAULT_DATASET)。"""
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    default = raw.pop("_default", "")
    for cfg in raw.values():
        cfg["output_dir"] = OUTPUT_DIR
    if not default or default not in raw:
        default = next(iter(raw), "")
    return raw, default


DATASET_CONFIGS, DEFAULT_DATASET = _load_configs()
CONFIG = DATASET_CONFIGS[DEFAULT_DATASET]

BASE_URL = "https://data.taipei/api/v1/dataset"
LIMIT    = 1000


# ─────────────────────────────────────────────
# 1. Extract
# 統一回傳 dict[source_id, DataFrame]
# ─────────────────────────────────────────────
def extract(config: dict) -> dict[str, pd.DataFrame]:
    """根據 source_type 分派，統一回傳 {source_id: DataFrame}。"""
    source_type = config.get("source_type", "data.taipei API")
    dag_id      = config["dag_id"]

    if source_type == "merged":
        return _extract_merged(config)
    elif source_type == "open_api":
        return {dag_id: _extract_open_api(config["api_url"])}
    elif source_type == "data.ntpc API":
        return {dag_id: _extract_ntpc(config["PAGE_ID"])}
    elif source_type == "other":
        print("[警告] 此資料集需自行實作 extract 邏輯。")
        return {}
    else:  # data.taipei API
        return {dag_id: _extract_data_taipei(config["RID"])}


def _extract_merged(config: dict) -> dict[str, pd.DataFrame]:
    """對每個子來源分別 extract，合併成一個 dict。"""
    results = {}
    for source_id in config["sources"]:
        results.update(extract(DATASET_CONFIGS[source_id]))
    return results


def _extract_data_taipei(rid: str) -> pd.DataFrame:
    """分頁取回 data.taipei 資料集。"""
    records = []
    offset  = 0

    while True:
        url    = f"{BASE_URL}/{rid}"
        params = {"scope": "resourceAquire", "limit": LIMIT, "offset": offset}
        resp   = requests.get(url, params=params, timeout=30, verify=False)
        resp.raise_for_status()

        data  = resp.json()
        if isinstance(data, list):
            batch = data
        else:
            batch = data.get("result", {}).get("results", [])
        if not batch:
            break

        records.extend(batch)
        offset += len(batch)
        if len(batch) < LIMIT:
            break

    df = pd.DataFrame(records)
    print(f"[Extract] 共取得 {len(records)} 筆原始資料，欄位：{list(df.columns)}")
    return df


def _extract_open_api(api_url: str) -> pd.DataFrame:
    """直接 GET 即時 API 並轉為 DataFrame。"""
    resp = requests.get(api_url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        for key in ("result", "data", "results", "records"):
            if key in data and isinstance(data[key], list):
                records = data[key]
                break
        else:
            records = [data]
    else:
        records = []

    print(f"[Extract] 共取得 {len(records)} 筆原始資料（Open API）")
    return pd.DataFrame(records)


def _extract_ntpc(ntpc_id: str) -> pd.DataFrame:
    """分頁取回 data.ntpc.gov.tw 資料集。"""
    records = []
    offset  = 0
    limit   = 1000
    url     = f"https://data.ntpc.gov.tw/api/datasets/{ntpc_id}/json"

    while True:
        resp  = requests.get(url, params={"limit": limit, "offset": offset},
                             timeout=30, verify=False)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        records.extend(batch)
        offset += len(batch)
        if len(batch) < limit:
            break

    df = pd.DataFrame(records)
    print(f"[Extract] 共取得 {len(records)} 筆原始資料（NTPC），欄位：{list(df.columns)}")
    return df


# ─────────────────────────────────────────────
# 2. Transform
# 有專屬策略檔 → 用 importlib 動態載入
# 無專屬策略檔 → 走 transform_single 通用清洗
# ─────────────────────────────────────────────
def transform(raw: dict[str, pd.DataFrame], data_time: str, config: dict) -> pd.DataFrame:
    """
    依 dag_id 尋找 transforms/{dag_id}.py。
    找到則呼叫其 transform(raw, data_time, config, DATASET_CONFIGS)。
    找不到則以 transform_single 通用清洗。
    """
    dag_id = config["dag_id"]
    try:
        mod = importlib.import_module(f"transforms.{dag_id}")
        return mod.transform(raw, data_time, config, DATASET_CONFIGS)
    except ModuleNotFoundError:
        df = next(iter(raw.values()))
        return transform_single(df, data_time, config)


# ─────────────────────────────────────────────
# 3. Load
# ─────────────────────────────────────────────
def load(df: pd.DataFrame, output_dir: str, table_name: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts       = datetime.now(tz=TAIPEI_TZ).strftime("%Y%m%d_%H%M%S")
    filename = f"{table_name}_{ts}.csv"
    filepath = os.path.join(output_dir, filename)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"[Load] 已輸出 {len(df)} 筆 → {filepath}")
    return filepath


# ─────────────────────────────────────────────
# 4. Update metadata
# ─────────────────────────────────────────────
def update_meta(df: pd.DataFrame, output_path: str, config: dict):
    meta_dir  = os.path.dirname(output_path)
    meta_path = os.path.join(meta_dir, "etl_meta.csv")

    lasttime = df["data_time"].max() if "data_time" in df.columns else ""
    meta = {
        "dag_id":           config["dag_id"],
        "output_file":      os.path.basename(output_path),
        "rows":             len(df),
        "lasttime_in_data": lasttime,
        "run_at":           datetime.now(tz=TAIPEI_TZ).isoformat(),
    }

    meta_df = pd.DataFrame([meta])
    if os.path.exists(meta_path):
        meta_df.to_csv(meta_path, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        meta_df.to_csv(meta_path, index=False, encoding="utf-8-sig")

    print(f"[Meta] ETL 紀錄已寫入 → {meta_path}")


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────
def main(config: dict):
    print("=" * 50)
    print(f"ETL 開始：{config['dag_id']}")
    print("=" * 50)

    raw = extract(config)
    if not raw:
        print("[警告] 無資料，ETL 中止。")
        return

    # merged 類型各子來源的 data_time 由策略檔各自處理
    if config.get("source_type") == "merged":
        data_time = datetime.now(tz=TAIPEI_TZ).isoformat()
    else:
        data_time = get_source_last_modified(config.get("PAGE_ID", ""))

    ready_df    = transform(raw, data_time, config)
    output_path = load(ready_df, config["output_dir"], config["output_table"])
    update_meta(ready_df, output_path, config)

    print("=" * 50)
    print("ETL 完成")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Taipei Dashboard ETL")
    parser.add_argument("--dag-id", type=str, default="", help="指定要執行的 dag_id（留空使用預設）")
    args = parser.parse_args()

    if args.dag_id:
        if args.dag_id not in DATASET_CONFIGS:
            print(f"[錯誤] dag_id「{args.dag_id}」不存在於 etl_config.json。")
            print(f"       可用：{list(DATASET_CONFIGS.keys())}")
        else:
            main(DATASET_CONFIGS[args.dag_id])
    else:
        main(CONFIG)
