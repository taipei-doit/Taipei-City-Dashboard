"""
transforms/雙北文化資產.py
==========================
臺北市文化資產 + 新北市文化資產 的合併 transform 策略。

column_map 與 keep_cols 由 etl_config.json 的 "雙北文化資產" 設定驅動，
城市標籤由本檔案的 _CITY_LABELS 維護。
"""

import pandas as pd
from transform_utils import get_source_last_modified, transform_single

_CITY_LABELS = {
    "臺北市文化資產": "臺北市",
    "新北市文化資產": "新北市",
}


def transform(
    raw: dict[str, pd.DataFrame],
    data_time: str,
    config: dict,
    dataset_configs: dict,
) -> pd.DataFrame:
    """
    1. 對每個子來源套用 column_map 重新命名欄位
    2. 補上「城市」欄位
    3. 各自走 transform_single 清洗
    4. concat 後依 keep_cols 輸出最終欄位
    """
    column_map = config.get("column_map", {})
    keep_cols  = config.get("keep_cols", [])
    parts      = []

    for source_id, df in raw.items():
        sub_config = dataset_configs[source_id]

        # 套用欄位重新命名（新北市 → 臺北市中文欄位名）
        mapping = column_map.get(source_id, {})
        df = df.rename(columns=mapping)

        # 補城市標籤
        df["城市"] = _CITY_LABELS.get(source_id, source_id)

        # data.taipei 來源取資料集本身的更新時間，其餘用傳入的 data_time
        if sub_config.get("source_type") == "data.taipei API":
            sub_data_time = get_source_last_modified(sub_config.get("PAGE_ID", ""))
        else:
            sub_data_time = data_time

        df = transform_single(df, sub_data_time, {"keep_cols": keep_cols})
        parts.append(df)

    merged = pd.concat(parts, ignore_index=True)
    merged = merged[[c for c in keep_cols if c in merged.columns]]

    print(f"[Transform] 合併後共 {len(merged)} 筆，欄位：{list(merged.columns)}")
    return merged
