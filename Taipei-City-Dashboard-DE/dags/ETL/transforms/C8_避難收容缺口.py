"""
transforms/C8_避難收容缺口.py
==============================
避難收容缺口分析：合併雙北收容處所資料 + 人口結構資料，
計算 65 歲以上弱勢人口 vs 收容容量的缺口指標。

實際欄位確認（2026-04-21）：
  C8_台北收容：行政區欄位=鄉鎮, 容量欄位=容納人數
  C8_新北收容：行政區欄位=district, 容量欄位=person
  C8_台北人口：行政區欄位=區域別, 需篩選性別=計, 加總 65~100歲以上欄位
  C8_新北人口：field1 格式="2000年 板橋區0 計", 65歲以上=percent28, 需篩選 計
"""

import re
import pandas as pd

_OUTPUT_COLS = [
    "data_time", "city_scope", "district_name",
    "shelter_count", "shelter_capacity",
    "vulnerable_population_65p",
    "capacity_gap_abs", "capacity_gap_ratio",
    "support_status", "source_trace", "data_mode",
]

# 65歲以上欄位列表（台北人口用）
_AGE_65_PLUS_COLS = [f"{age}歲數量" for age in range(65, 100)] + ["100歲以上"]


def _normalize_district(raw) -> str:
    """去除縣市前綴，只保留區名。"""
    s = str(raw).strip()
    s = re.sub(r"^(臺北市|台北市|新北市)", "", s).strip()
    return s


# ── 台北市收容處所 ────────────────────────────────────────────────────────────

def _parse_taipei_shelter(df: pd.DataFrame) -> pd.DataFrame:
    """
    欄位：鄉鎮（行政區）、容納人數（容量）
    """
    df = df.copy()
    df["_dist"] = df["鄉鎮"].apply(_normalize_district)
    df["_cap"]  = pd.to_numeric(df["容納人數"], errors="coerce").fillna(0).astype(int)

    result = df.groupby("_dist", as_index=False).agg(
        shelter_count=("_cap", "count"),
        shelter_capacity=("_cap", "sum"),
    ).rename(columns={"_dist": "district"})
    result["city_scope"] = "Taipei"
    print(f"  [台北收容] {len(result)} 個行政區")
    return result


# ── 新北市收容處所 ────────────────────────────────────────────────────────────

def _parse_ntpc_shelter(df: pd.DataFrame) -> pd.DataFrame:
    """
    欄位：district（行政區）、person（容量）
    """
    df = df.copy()
    df["_dist"] = df["district"].apply(_normalize_district)
    df["_cap"]  = pd.to_numeric(df["person"], errors="coerce").fillna(0).astype(int)

    result = df.groupby("_dist", as_index=False).agg(
        shelter_count=("_cap", "count"),
        shelter_capacity=("_cap", "sum"),
    ).rename(columns={"_dist": "district"})
    result["city_scope"] = "NewTaipei"
    print(f"  [新北收容] {len(result)} 個行政區")
    return result


# ── 台北市人口（65歲以上） ────────────────────────────────────────────────────

def _parse_taipei_population(df: pd.DataFrame) -> pd.DataFrame:
    """
    篩選 性別=計、區域別 != 總計
    65歲以上人口 = 加總 65歲數量 ~ 100歲以上
    """
    df = df.copy()
    # 篩選「計」且排除「總計」
    df = df[(df["性別"] == "計") & (df["區域別"] != "總計")]

    # 只取最新年份最新月份，避免多年份資料累加
    latest_year = df["年份"].max()
    df = df[df["年份"] == latest_year]
    latest_month = df["月份"].max()
    df = df[df["月份"] == latest_month]
    print(f"  [台北人口] 使用 {latest_year}年{latest_month}月 資料")

    # 加總 65 歲以上各欄位
    age_cols = [c for c in _AGE_65_PLUS_COLS if c in df.columns]
    for c in age_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["vulnerable_population_65p"] = df[age_cols].sum(axis=1).astype(int)

    result = df[["區域別", "vulnerable_population_65p"]].copy()
    result["district"] = result["區域別"].apply(_normalize_district)
    result = result.groupby("district", as_index=False)["vulnerable_population_65p"].sum()
    print(f"  [台北人口] {len(result)} 個行政區，65歲以上總計：{result['vulnerable_population_65p'].sum()}")
    return result


# ── 新北市人口（65歲以上） ────────────────────────────────────────────────────

def _parse_ntpc_population(df: pd.DataFrame) -> pd.DataFrame:
    """
    field1 格式："2000年 板橋區0 計"
    篩選「計」、排除「新北市0」（全市總計）
    percent28 = 65歲以上人口數
    """
    df = df.copy()

    # 解析 field1：取出區名和性別
    # 格式："{年份}年 {地區}0 {性別}"
    def parse_field1(s):
        m = re.match(r"\d+年\s+(.+?)0\s+(計|男|女)", str(s))
        if m:
            return m.group(1).strip(), m.group(2)
        return None, None

    df[["_area", "_gender"]] = df["field1"].apply(
        lambda x: pd.Series(parse_field1(x))
    )

    # 篩選「計」並排除全市總計
    df = df[(df["_gender"] == "計") & (df["_area"] != "新北市")]

    df["vulnerable_population_65p"] = pd.to_numeric(df["percent28"], errors="coerce").fillna(0).astype(int)
    df["district"] = df["_area"].apply(_normalize_district)

    # 只取最新年份（避免多年資料重複）
    if "field1" in df.columns:
        # 解析年份
        df["_year"] = df["field1"].str.extract(r"(\d+)年").astype(float)
        latest_year = df["_year"].max()
        df = df[df["_year"] == latest_year]

    result = df.groupby("district", as_index=False)["vulnerable_population_65p"].sum()
    print(f"  [新北人口] {len(result)} 個行政區，65歲以上總計：{result['vulnerable_population_65p'].sum()}")
    return result


# ── 缺口計算 ──────────────────────────────────────────────────────────────────

def _calc_gap(row) -> pd.Series:
    pop     = int(row["vulnerable_population_65p"])
    cap     = int(row["shelter_capacity"])
    gap_abs = pop - cap
    gap_ratio = round(gap_abs / pop, 4) if pop > 0 else 0.0

    if gap_abs <= 0:
        status = "surplus"
    elif gap_ratio < 0.1:
        status = "tight"
    elif gap_ratio < 0.3:
        status = "gap"
    else:
        status = "critical_gap"

    return pd.Series({
        "capacity_gap_abs":   gap_abs,
        "capacity_gap_ratio": gap_ratio,
        "support_status":     status,
    })


# ── 主 transform ──────────────────────────────────────────────────────────────

def transform(
    raw: dict[str, pd.DataFrame],
    data_time: str,
    config: dict,
    dataset_configs: dict,
) -> pd.DataFrame:

    tp_shelter   = _parse_taipei_shelter(raw["C8_台北收容"])
    ntpc_shelter = _parse_ntpc_shelter(raw["C8_新北收容"])
    tp_pop       = _parse_taipei_population(raw["C8_台北人口"])
    ntpc_pop     = _parse_ntpc_population(raw["C8_新北人口"])

    def _merge_city(shelter_df, pop_df, city_scope, source_trace):
        merged = shelter_df.merge(pop_df, on="district", how="outer")
        merged["city_scope"]                = city_scope
        merged["shelter_count"]             = merged["shelter_count"].fillna(0).astype(int)
        merged["shelter_capacity"]          = merged["shelter_capacity"].fillna(0).astype(int)
        merged["vulnerable_population_65p"] = merged["vulnerable_population_65p"].fillna(0).astype(int)
        merged[["capacity_gap_abs", "capacity_gap_ratio", "support_status"]] = merged.apply(_calc_gap, axis=1)
        merged["source_trace"] = source_trace
        return merged

    tp_result   = _merge_city(tp_shelter,   tp_pop,   "Taipei",    "data.taipei（收容處所 + 人口統計）")
    ntpc_result = _merge_city(ntpc_shelter, ntpc_pop, "NewTaipei", "data.ntpc（收容處所 + 人口統計）")

    final = pd.concat([tp_result, ntpc_result], ignore_index=True)
    final = final.rename(columns={"district": "district_name"})

    # 排除空白行政區
    final = final[final["district_name"].astype(str).str.strip() != ""]

    final["data_time"] = data_time
    final["data_mode"] = "real"

    final = final[[c for c in _OUTPUT_COLS if c in final.columns]].reset_index(drop=True)

    status_counts = final["support_status"].value_counts().to_dict()
    print(f"[Transform] C8 完成，共 {len(final)} 個行政區，support_status 分布：{status_counts}")
    return final