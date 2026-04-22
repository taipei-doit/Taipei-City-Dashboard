"""
transforms/C3_文化設施密度.py
==============================
雙北文化設施密度比較的 transform 策略。

【欄位映射規則】（雙北不一致，統一輸出欄位如下）
  臺北市文化資產  →  統一欄位
  ─────────────────────────
  個案名稱        →  facility_name
  資產類別        →  facility_type
  資產種類        →  facility_subtype
  所在地理區域    →  district  （直接使用）

  新北市文化資產  →  統一欄位
  ─────────────────────────
  名稱            →  facility_name
  文化資產        →  facility_type
  類別            →  facility_subtype
  地址            →  raw_address  （擷取前三字作為行政區）

輸出層次：每行政區一列，含設施數量與類型清單。
輸出表：hackathon_component_3_cultural_density_ready
"""

import re
import pandas as pd
from datetime import datetime
from transform_utils import TAIPEI_TZ, transform_single

# 新北市地址中的行政區正規表達式（三字區名）
_NTPC_DISTRICT_RE = re.compile(r"新北市([^\s市]{2,3}區)")


def _parse_ntpc_district(address: str) -> str:
    """從新北市地址字串擷取行政區名稱。"""
    if not address:
        return "未知"
    m = _NTPC_DISTRICT_RE.search(str(address))
    if m:
        return m.group(1)
    # 退而求其次：取前三字（去掉「新北市」前綴）
    addr = str(address).replace("新北市", "").strip()
    return addr[:3] if len(addr) >= 3 else addr or "未知"


_COLUMN_MAP = {
    "臺北市文化資產": {
        "個案名稱":   "facility_name",
        "資產類別":   "facility_type",
        "資產種類":   "facility_subtype",
        "所在地理區域": "district",
    },
    "新北市文化資產": {
        # 新北市 API 回傳英文欄位
        "name":      "facility_name",
        "affection": "facility_type",
        "category":  "facility_subtype",
        "address":   "_raw_address",   # 稍後從地址擷取行政區
    },
}

_CITY_LABELS = {
    "臺北市文化資產": "Taipei",
    "新北市文化資產": "NewTaipei",
}


def transform(
    raw: dict[str, pd.DataFrame],
    data_time: str,
    config: dict,
    dataset_configs: dict,
) -> pd.DataFrame:
    parts = []

    for source_id, df in raw.items():
        df = df.copy()
        mapping = _COLUMN_MAP.get(source_id, {})
        df = df.rename(columns=mapping)

        df["city_scope"] = _CITY_LABELS.get(source_id, source_id)

        # 新北市：從 _raw_address 擷取行政區
        if "_raw_address" in df.columns:
            df["district"] = df["_raw_address"].apply(_parse_ntpc_district)
            df = df.drop(columns=["_raw_address"])

        # 確保必要欄位存在
        for col in ("facility_name", "facility_type", "facility_subtype", "district"):
            if col not in df.columns:
                df[col] = ""

        df = df[["city_scope", "district", "facility_name", "facility_type", "facility_subtype"]]
        df = df.dropna(subset=["facility_name"])
        df = df[df["facility_name"].str.strip() != ""]
        parts.append(df)

    combined = pd.concat(parts, ignore_index=True)

    # 按城市+行政區聚合：計算設施數量與類型清單
    agg = (
        combined.groupby(["city_scope", "district"])
        .agg(
            facility_count=("facility_name", "count"),
            facility_types=("facility_type", lambda x: "、".join(sorted(set(x.dropna())))),
        )
        .reset_index()
    )

    agg["source_trace"] = "data.taipei + data.ntpc（文化資產資料集）"
    agg["data_mode"]    = "real"
    agg["last_updated"] = datetime.now(tz=TAIPEI_TZ).isoformat()

    print(f"[Transform] C3 文化設施密度，共 {len(agg)} 個行政區記錄")
    return agg
