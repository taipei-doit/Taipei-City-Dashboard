"""
C7_雙北藥局分布與可及性分析 — Transform 模組
raw key 對應 etl_config.json 的 dag_id：
  "臺北市藥局"           → 機構名稱 / 地址 / x / y
  "新北市健保特約藥局名單" → name / address / district / longitude_wgs84ax / latitude_wgs84ay
  "新北市非健保特約藥局名單" → name / address / wgs84ax_longitude / wgs84ay
輸出 Schema（單一表）：
  data_time, id, name, address, telephone, longitude, latitude,
  district, city, nhi, pharmacy_per_10k
"""

import pandas as pd
import re
import sys
import os

sys.path.insert(0, os.path.dirname(__file__) + "/..")
from transform_utils import convert_str_to_time_format

# ── 人口數據（2024年底）──────────────────────────────────────
POPULATION = {
    "中正區": 153407, "大同區": 115490, "中山區": 203718, "松山區": 196685,
    "大安區": 289534, "萬華區": 183960, "信義區": 214340, "士林區": 279497,
    "北投區": 253124, "內湖區": 286977, "南港區": 114783, "文山區": 273278,
    "板橋區": 547894, "三重區": 384523, "中和區": 397154, "永和區": 226553,
    "新莊區": 426264, "蘆洲區": 205083, "樹林區": 188273, "鶯歌區": 83888,
    "三峽區": 102498, "淡水區": 185094, "汐止區": 200754, "瑞芳區": 43786,
    "新店區": 304010, "土城區": 238695, "林口區": 116396, "泰山區": 77027,
    "五股區": 73067,  "深坑區": 25490,  "石碇區": 10201,  "坪林區": 6541,
    "三芝區": 23069,  "石門區": 12249,  "八里區": 40001,  "平溪區": 6768,
    "雙溪區": 9785,   "貢寮區": 12119,  "金山區": 22155,  "萬里區": 22705,
    "烏來區": 5484,
}

def extract_district(address: str) -> str:
    m = re.search(r'([^\s市]+(?:區|鄉|鎮))', str(address))
    return m.group(1) if m else "未知"

def clean_phone(phone) -> str:
    if pd.isna(phone):
        return ""
    return str(phone).strip().replace("-", "").replace(" ", "")

# ── 各來源標準化 ──────────────────────────────────────────────

def _process_taipei(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame({
        "name":      df["機構名稱"].str.strip(),
        "address":   df["地址"].str.strip(),
        "telephone": df["電話"].apply(clean_phone),
        "longitude": pd.to_numeric(df["x"], errors="coerce"),
        "latitude":  pd.to_numeric(df["y"], errors="coerce"),
        "city":      "臺北市",
        "nhi":       True,
    })
    result["district"] = result["address"].apply(extract_district)
    return result

def _process_new_taipei_nhi(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame({
        "name":      df["name"].str.strip(),
        "address":   df["address"].str.strip(),
        "telephone": df["telephone"].apply(clean_phone),
        "longitude": pd.to_numeric(df["longitude_wgs84ax"], errors="coerce"),
        "latitude":  pd.to_numeric(df["latitude_wgs84ay"],  errors="coerce"),
        "city":      "新北市",
        "nhi":       True,
    })
    # 優先用原始 district 欄，缺值時從地址抽取
    result["district"] = df["district"].str.strip().where(
        df["district"].notna(), result["address"].apply(extract_district)
    )
    return result

def _process_new_taipei_non_nhi(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame({
        "name":      df["name"].str.strip(),
        "address":   df["address"].str.strip(),
        "telephone": df["telephone"].apply(clean_phone),
        "longitude": pd.to_numeric(df["wgs84ax_longitude"], errors="coerce"),
        "latitude":  pd.to_numeric(df["wgs84ay"],           errors="coerce"),
        "city":      "新北市",
        "nhi":       False,
    })
    result["district"] = result["address"].apply(extract_district)
    return result

def _attach_pharmacy_per_10k(df: pd.DataFrame) -> pd.DataFrame:
    counts = df.groupby(["city", "district"])["id"].count().reset_index(name="pharmacy_count")
    counts["population"] = counts["district"].map(POPULATION)
    counts["pharmacy_per_10k"] = (
        counts["pharmacy_count"] / counts["population"] * 10000
    ).where(counts["population"].notna()).round(2)
    return df.merge(counts[["city", "district", "pharmacy_per_10k"]], on=["city", "district"], how="left")

# ── Transform 主函式 ──────────────────────────────────────────

def transform(raw: dict, data_time: str, **kwargs) -> pd.DataFrame:
    print("[C7 轉換開始] 雙北藥局分布與可及性分析")

    # key 對應 etl_config.json 的 dag_id
    tp_df           = raw.get("臺北市藥局",           pd.DataFrame())
    ntpc_nhi_df     = raw.get("新北市健保特約藥局名單", pd.DataFrame())
    ntpc_non_nhi_df = raw.get("新北市非健保特約藥局名單", pd.DataFrame())

    parts = []
    if not tp_df.empty:
        parts.append(_process_taipei(tp_df))
    if not ntpc_nhi_df.empty:
        parts.append(_process_new_taipei_nhi(ntpc_nhi_df))
    if not ntpc_non_nhi_df.empty:
        parts.append(_process_new_taipei_non_nhi(ntpc_non_nhi_df))

    if not parts:
        print("[C7 轉換] ⚠️ 無資料")
        return pd.DataFrame()

    df = pd.concat(parts, ignore_index=True)

    # 座標驗證
    df = df.dropna(subset=["longitude", "latitude"])
    df = df[df["longitude"].between(119.0, 122.5) & df["latitude"].between(21.5, 25.5)]

    # 去重
    df = df.drop_duplicates(subset=["name", "address"])

    # ID + data_time
    df = df.reset_index(drop=True)
    df.insert(0, "id", df.index + 1)
    df["data_time"] = convert_str_to_time_format(pd.Series([data_time] * len(df)))

    # 各區每萬人藥局數
    df = _attach_pharmacy_per_10k(df)

    print(f"[C7 轉換完成] ✓ 藥局數：{len(df)}")
    print(f"  城市分布：{df['city'].value_counts().to_dict()}")
    print(f"  NHI：{df['nhi'].sum()} 家，非NHI：{(~df['nhi']).sum()} 家")

    return df


if __name__ == "__main__":
    print("C7 Transform 模組 — 請透過 ETL.py 呼叫")