"""
transform_utils.py
==================
各 transform 策略共用的工具函式，避免與 ETL.py 產生循環依賴。
"""

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import pandas as pd
from datetime import datetime, timezone, timedelta

TAIPEI_TZ = timezone(timedelta(hours=8))


def get_source_last_modified(page_id: str) -> str:
    """取得 data.taipei 資料集最後更新時間（無 PAGE_ID 時回傳當下時間）。"""
    if not page_id:
        return datetime.now(tz=TAIPEI_TZ).isoformat()
    url = f"https://data.taipei/api/v1/dataset/{page_id}"
    try:
        resp = requests.get(url, timeout=10, verify=False)
        resp.raise_for_status()
        return resp.json().get("result", {}).get("modified", "") or datetime.now(tz=TAIPEI_TZ).isoformat()
    except Exception:
        return datetime.now(tz=TAIPEI_TZ).isoformat()


def transform_single(df: pd.DataFrame, data_time: str, config: dict) -> pd.DataFrame:
    """
    單一來源的通用清洗流程：
    - 寫入 data_time
    - 刪除系統欄位
    - lng/lat 轉數值
    - 依 keep_cols 篩選欄位
    - 刪除 個案名稱 為空的列
    """
    df        = df.copy()
    keep_cols = config.get("keep_cols", list(df.columns))

    try:
        dt = datetime.fromisoformat(data_time)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TAIPEI_TZ)
        df["data_time"] = dt.isoformat()
    except ValueError:
        df["data_time"] = datetime.now(tz=TAIPEI_TZ).isoformat()

    df = df.drop(columns=[c for c in ["_id", "_importdate", "objectid"] if c in df.columns])

    if "lng" in df.columns:
        df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    if "lat" in df.columns:
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")

    df = df[[c for c in keep_cols if c in df.columns]]

    if "個案名稱" in df.columns:
        df = df.dropna(subset=["個案名稱"])

    print(f"[Transform] 清洗後剩餘 {len(df)} 筆，欄位：{list(df.columns)}")
    return df
