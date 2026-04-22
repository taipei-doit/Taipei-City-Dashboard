"""
transforms/C1_藝文活動.py
==========================
文化部雲端藝文活動資料集（cloud.culture.tw）的 transform 策略。
使用 explode("showInfo") 展開巢狀場次清單。

輸出表：hackathon_component_1_event_map_ready
"""

import json
import pandas as pd

_OUTPUT_COLS = [
    "data_time", "title", "location_name", "latitude", "longitude",
    "event_time", "category", "on_sales", "source_trace", "data_mode",
]


def _parse_show_info(x) -> list:
    """確保每個 showInfo 欄位都是 list[dict]，空值補 [{}]。"""
    if isinstance(x, list):
        return x or [{}]
    if isinstance(x, str):
        try:
            result = json.loads(x)
            return result if result else [{}]
        except Exception:
            return [{}]
    return [{}]


def transform(
    raw: dict[str, pd.DataFrame],
    data_time: str,
    config: dict,
    dataset_configs: dict,
) -> pd.DataFrame:
    df = raw[config["dag_id"]].copy()
    print(df.columns.tolist())

    # 展開 showInfo[]
    df["showInfo"] = df["showInfo"].apply(_parse_show_info)
    df = df.explode("showInfo").reset_index(drop=True)

    # 從 showInfo dict 取出各欄位
    def _get(d, key, default=""):
        return d.get(key, default) if isinstance(d, dict) else default

    df["location_name"] = df["showInfo"].apply(lambda x: _get(x, "locationName"))
    df["latitude"]      = df["showInfo"].apply(lambda x: _get(x, "latitude",  None))
    df["longitude"]     = df["showInfo"].apply(lambda x: _get(x, "longitude", None))
    df["event_time"]    = df["showInfo"].apply(lambda x: _get(x, "time"))

    # 數值轉換
    df["latitude"]  = pd.to_numeric(df["latitude"],  errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # 過濾無效座標
    df = df.dropna(subset=["latitude", "longitude"]).copy()

    # on_sales → boolean
    on_sales_col = "onSales" if "onSales" in df.columns else None
    df["on_sales"] = (
        df[on_sales_col].apply(lambda x: str(x).strip().upper() == "Y")
        if on_sales_col else False
    )

    # 欄位補齊
    df["data_time"]    = data_time
    df["source_trace"] = "cloud.culture.tw"
    df["data_mode"]    = "real"

    result = df[[c for c in _OUTPUT_COLS if c in df.columns]].reset_index(drop=True)
    print(f"[Transform] C1 藝文活動，展開後共 {len(result)} 筆有效資料（含經緯度）")
    return result
