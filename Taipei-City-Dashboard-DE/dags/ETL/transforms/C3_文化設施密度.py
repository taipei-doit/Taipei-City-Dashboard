import re
import pandas as pd


def extract_district(text):
    """從地址字串擷取行政區（XX區/XX鄉/XX鎮/XX市）。"""
    if pd.isna(text):
        return None
    m = re.search(r"([^\s市縣]+[鄉鎮市區])", str(text))
    return m.group(1) if m else str(text).strip()


OUTPUT_COLS = [
    "data_time", "city_scope", "city", "district",
    "asset_name", "asset_category", "asset_type",
    "address", "source_trace", "data_mode",
]


def transform(
    raw: dict[str, pd.DataFrame],
    data_time: str,
    config: dict,
    dataset_configs: dict,
) -> pd.DataFrame:
    tp_df = raw["臺北市文化資產"].copy()
    ntpc_df = raw["新北市文化資產"].copy()

    # --- 臺北市 ---
    tp_df = tp_df.rename(columns={
        "個案名稱":   "asset_name",
        "資產類別":   "asset_category",
        "資產種類":   "asset_type",
        "所在地理區域": "address",
    })
    tp_df["city"]        = "臺北市"
    tp_df["city_scope"]  = "Taipei"
    tp_df["source_trace"] = "data.taipei（臺北市文化資產）"
    tp_df["district"]    = tp_df["address"].apply(extract_district)

    # --- 新北市 ---
    ntpc_df["asset_category"] = ntpc_df["rank"].map({
        "縣定": "縣定古蹟",
        "市定": "直轄市定古蹟",
    }).fillna(ntpc_df["affection"])

    ntpc_df = ntpc_df.rename(columns={
        "name":     "asset_name",
        "category": "asset_type",
        "address":  "address",
    })
    ntpc_df["city"]        = "新北市"
    ntpc_df["city_scope"]  = "NewTaipei"
    ntpc_df["source_trace"] = "data.ntpc（新北市文化資產）"
    ntpc_df["district"]    = ntpc_df["address"].apply(extract_district)

    # --- 合併 ---
    for df in (tp_df, ntpc_df):
        df["data_time"] = data_time
        df["data_mode"] = "real"

    final = pd.concat(
        [tp_df[OUTPUT_COLS], ntpc_df[OUTPUT_COLS]],
        ignore_index=True,
    )

    print(f"[Transform] C3 文化設施密度，共 {len(final)} 筆（臺北 {len(tp_df)} + 新北 {len(ntpc_df)}）")
    return final
