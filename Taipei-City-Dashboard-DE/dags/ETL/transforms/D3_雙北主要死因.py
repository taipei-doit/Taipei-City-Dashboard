"""
transforms/D3_雙北主要死因.py
==============================
合併台北市與新北市主要死亡原因統計，輸出年度死因趨勢表。

台北來源：臺北市歷年死亡概況（衛生局）
  欄位：年份、性別（合計/男/女列）、疾病死因、順位、死亡人數、死亡率…
  或    臺北市主要死亡原因（主計處）
  欄位：統計期、死因別、順位、死亡人數/合計[人]、死亡人數/男[人]、死亡人數/女[人]、死亡率/合計[人/十萬人口]

新北來源：死亡人數—主要死因（主計處）
  欄位：執行時以 print() 確認（預期含年份、性別、死因、死亡人數）
"""

import re
import pandas as pd


# ── 死因標準化對照表 ──────────────────────────────────────────────────────────

CAUSE_MAP = {
    # 惡性腫瘤 / 癌症
    "惡性腫瘤":     "惡性腫瘤",
    "癌症":         "惡性腫瘤",
    "惡性腫瘤[癌症]": "惡性腫瘤",
    # 心臟疾病
    "心臟疾病":     "心臟疾病",
    "心臟病":       "心臟疾病",
    "心臟衰竭":     "心臟疾病",
    # 腦血管疾病
    "腦血管疾病":   "腦血管疾病",
    "中風":         "腦血管疾病",
    "腦血管":       "腦血管疾病",
    # 肺炎
    "肺炎":         "肺炎",
    # 糖尿病
    "糖尿病":       "糖尿病",
    # 慢性下呼吸道疾病
    "慢性下呼吸道疾病": "慢性下呼吸道疾病",
    "慢性阻塞性肺病":   "慢性下呼吸道疾病",
    # 腎臟疾病
    "腎炎腎徵候群及腎性病變": "腎臟疾病",
    "腎臟疾病":     "腎臟疾病",
    "腎炎":         "腎臟疾病",
    # 敗血症
    "敗血症":       "敗血症",
    # 高血壓
    "高血壓性疾病": "高血壓性疾病",
    "高血壓":       "高血壓性疾病",
    # 事故傷害
    "事故傷害":     "事故傷害",
    "意外事故":     "事故傷害",
    "意外傷害":     "事故傷害",
    # 慢性肝病
    "慢性肝病及肝硬化": "慢性肝病及肝硬化",
    "肝硬化":       "慢性肝病及肝硬化",
    "慢性肝病":     "慢性肝病及肝硬化",
    # 自殺
    "自殺":         "自殺",
    "蓄意自我傷害": "自殺",
    # 結核病
    "結核病":       "結核病",
}


def _normalize_cause(raw_cause: str) -> str:
    s = str(raw_cause).strip()
    # 完整比對
    if s in CAUSE_MAP:
        return CAUSE_MAP[s]
    # 部分比對（從最長的 key 開始）
    for key in sorted(CAUSE_MAP, key=len, reverse=True):
        if key in s:
            return CAUSE_MAP[key]
    return s


def _roc_to_ad(val) -> int | None:
    s = str(val).strip().replace("年", "").replace("民國", "").strip()
    m = re.search(r"(\d+)", s)
    if not m:
        return None
    n = int(m.group(1))
    return n if n > 1911 else n + 1911


def _pick_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    norm = {c.strip().lower(): c for c in df.columns}
    for cand in candidates:
        if cand.strip().lower() in norm:
            return norm[cand.strip().lower()]
    return None


def _to_int(val) -> int | None:
    try:
        f = float(str(val).replace(",", "").strip())
        return int(f) if f == f else None
    except (TypeError, ValueError):
        return None


def _to_float(val) -> float | None:
    try:
        f = float(str(val).replace(",", "").strip())
        return None if f != f else f
    except (TypeError, ValueError):
        return None


# ── 台北市 ────────────────────────────────────────────────────────────────────

def _parse_taipei_wide(df: pd.DataFrame) -> pd.DataFrame:
    """
    寬格式（臺北市主要死亡原因，主計處）：
    統計期、死因別、順位、死亡人數/合計[人]、死亡人數/男[人]、死亡人數/女[人]、死亡率/合計[人/十萬人口]
    """
    period_col  = _pick_col(df, ["統計期"])
    cause_col   = _pick_col(df, ["死因別", "疾病死因", "死亡原因"])
    rank_col    = _pick_col(df, ["順位", "主要死亡原因順位"])
    total_col   = _pick_col(df, ["死亡人數/合計[人]", "死亡人數/合計", "合計"])
    male_col    = _pick_col(df, ["死亡人數/男[人]", "死亡人數/男", "男"])
    female_col  = _pick_col(df, ["死亡人數/女[人]", "死亡人數/女", "女"])
    rate_col    = _pick_col(df, ["死亡率/合計[人/十萬人口]", "死亡率/合計", "死亡率"])

    rows = []
    for _, r in df.iterrows():
        year = _roc_to_ad(r[period_col]) if period_col else None
        if year is None:
            continue
        rows.append({
            "year":               year,
            "cause_of_death":     _normalize_cause(r[cause_col]) if cause_col else None,
            "cause_rank":         _to_int(r[rank_col]) if rank_col else None,
            "death_count_total":  _to_int(r[total_col]) if total_col else None,
            "death_count_male":   _to_int(r[male_col]) if male_col else None,
            "death_count_female": _to_int(r[female_col]) if female_col else None,
            "death_rate":         _to_float(r[rate_col]) if rate_col else None,
        })
    return pd.DataFrame(rows)


def _parse_taipei_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    長格式（臺北市歷年死亡概況，衛生局）：
    年份、性別（合計/男/女）、疾病死因、順位、死亡人數、死亡率
    需要 pivot 將性別展開為欄位。
    """
    year_col  = _pick_col(df, ["年份", "年度"])
    sex_col   = _pick_col(df, ["性別"])
    cause_col = _pick_col(df, ["疾病死因", "死因別", "死亡原因"])
    rank_col  = _pick_col(df, ["順位"])
    count_col = _pick_col(df, ["死亡人數"])
    rate_col  = _pick_col(df, ["死亡率"])

    df = df.copy()
    df["_year"]  = df[year_col].apply(_roc_to_ad) if year_col else None
    df["_cause"] = df[cause_col].apply(_normalize_cause) if cause_col else ""
    df["_rank"]  = df[rank_col].apply(_to_int) if rank_col else None
    df["_count"] = df[count_col].apply(_to_int) if count_col else None
    df["_rate"]  = df[rate_col].apply(_to_float) if rate_col else None
    df["_sex"]   = df[sex_col].str.strip() if sex_col else "合計"

    df = df.dropna(subset=["_year"])

    group_keys = ["_year", "_cause", "_rank"]
    pivoted = df.pivot_table(
        index=group_keys,
        columns="_sex",
        values=["_count", "_rate"],
        aggfunc="first",
    )
    pivoted.columns = ["_".join(str(c) for c in col).strip() for col in pivoted.columns]
    pivoted = pivoted.reset_index()

    def _pick_pivoted(df_pv, candidates):
        for c in candidates:
            if c in df_pv.columns:
                return c
        return None

    total_col  = _pick_pivoted(pivoted, ["_count_合計", "_count_total"])
    male_col   = _pick_pivoted(pivoted, ["_count_男", "_count_male"])
    female_col = _pick_pivoted(pivoted, ["_count_女", "_count_female"])
    rate_col   = _pick_pivoted(pivoted, ["_rate_合計", "_rate_total"])

    rows = []
    for _, r in pivoted.iterrows():
        rows.append({
            "year":               int(r["_year"]),
            "cause_of_death":     r["_cause"],
            "cause_rank":         r["_rank"],
            "death_count_total":  _to_int(r.get(total_col)) if total_col else None,
            "death_count_male":   _to_int(r.get(male_col)) if male_col else None,
            "death_count_female": _to_int(r.get(female_col)) if female_col else None,
            "death_rate":         _to_float(r.get(rate_col)) if rate_col else None,
        })
    return pd.DataFrame(rows)


def _parse_taipei(df: pd.DataFrame) -> pd.DataFrame:
    print(f"[台北死因] 欄位：{df.columns.tolist()}")

    # 判斷格式：有「死亡人數/合計[人]」風格 → 寬格式；有「性別」欄位 → 長格式
    has_wide = any("/" in c for c in df.columns)
    has_long = _pick_col(df, ["性別"]) is not None

    if has_wide and not has_long:
        result = _parse_taipei_wide(df)
        print(f"  [台北死因] 寬格式，解析 {len(result)} 筆")
    else:
        result = _parse_taipei_long(df)
        print(f"  [台北死因] 長格式，解析 {len(result)} 筆")

    result["city_scope"]   = "Taipei"
    result["city"]         = "臺北市"
    result["source_trace"] = "data.taipei（臺北市主要死亡原因，主計處/衛生局）"
    return result


# ── 新北市 ────────────────────────────────────────────────────────────────────

def _parse_ntpc(df: pd.DataFrame) -> pd.DataFrame:
    print(f"[新北死因] 欄位：{df.columns.tolist()}")

    year_col  = _pick_col(df, ["年份", "年度", "year"])
    sex_col   = _pick_col(df, ["性別", "sex", "gender"])
    cause_col = _pick_col(df, ["死因", "死因別", "疾病死因", "死亡原因", "cause"])
    rank_col  = _pick_col(df, ["順位", "rank", "死亡順位"])
    count_col = _pick_col(df, ["死亡人數", "人數", "count", "deaths"])
    rate_col  = _pick_col(df, ["死亡率", "rate"])

    print(f"  [新北死因] 對應: year={year_col}, sex={sex_col}, cause={cause_col}, "
          f"rank={rank_col}, count={count_col}, rate={rate_col}")

    df = df.copy()
    df["_year"]  = df[year_col].apply(_roc_to_ad) if year_col else None
    df["_cause"] = df[cause_col].apply(_normalize_cause) if cause_col else ""
    df["_rank"]  = df[rank_col].apply(_to_int) if rank_col else None
    df["_count"] = df[count_col].apply(_to_int) if count_col else None
    df["_rate"]  = df[rate_col].apply(_to_float) if rate_col else None
    df["_sex"]   = df[sex_col].str.strip() if sex_col else "合計"

    df = df.dropna(subset=["_year"])

    if sex_col and df["_sex"].nunique() > 1:
        # 長格式（含性別列），pivot 展開
        group_keys = ["_year", "_cause", "_rank"]
        pivoted = df.pivot_table(
            index=group_keys,
            columns="_sex",
            values="_count",
            aggfunc="first",
        ).reset_index()

        def _pc(candidates):
            for c in candidates:
                if c in pivoted.columns:
                    return c
            return None

        total_col  = _pc(["合計", "total", "Total"])
        male_col   = _pc(["男", "male", "Male"])
        female_col = _pc(["女", "female", "Female"])

        # 死亡率：取合計列的 rate
        rate_map = (
            df[df["_sex"].isin(["合計", "total", "Total"])]
            .groupby(["_year", "_cause"])["_rate"]
            .first()
            .to_dict()
        )

        rows = []
        for _, r in pivoted.iterrows():
            rows.append({
                "year":               int(r["_year"]),
                "cause_of_death":     r["_cause"],
                "cause_rank":         r.get("_rank"),
                "death_count_total":  _to_int(r.get(total_col)) if total_col else None,
                "death_count_male":   _to_int(r.get(male_col)) if male_col else None,
                "death_count_female": _to_int(r.get(female_col)) if female_col else None,
                "death_rate":         rate_map.get((r["_year"], r["_cause"])),
            })
        result = pd.DataFrame(rows)
    else:
        # 每列就是合計
        rows = []
        for _, r in df.iterrows():
            if r["_year"] is None:
                continue
            rows.append({
                "year":               int(r["_year"]),
                "cause_of_death":     r["_cause"],
                "cause_rank":         r["_rank"],
                "death_count_total":  r["_count"],
                "death_count_male":   None,
                "death_count_female": None,
                "death_rate":         r["_rate"],
            })
        result = pd.DataFrame(rows)

    result["city_scope"]   = "NewTaipei"
    result["city"]         = "新北市"
    result["source_trace"] = "data.ntpc（新北市死亡人數主要死因，主計處）"
    print(f"  [新北死因] 解析 {len(result)} 筆")
    return result


# ── 主 transform ──────────────────────────────────────────────────────────────

def transform(
    raw: dict[str, pd.DataFrame],
    data_time: str,
    config: dict,
    dataset_configs: dict,
) -> pd.DataFrame:

    tp_df   = _parse_taipei(raw["D3_台北死因"])
    ntpc_df = _parse_ntpc(raw["D3_新北死因"])

    final = pd.concat([tp_df, ntpc_df], ignore_index=True)
    final["data_time"] = data_time
    final["data_mode"] = "real"

    final = final[[
        "data_time", "city_scope", "city", "year",
        "cause_of_death", "cause_rank",
        "death_count_total", "death_count_male", "death_count_female",
        "death_rate", "source_trace", "data_mode",
    ]].reset_index(drop=True)

    by_city = final.groupby("city_scope").size().to_dict()
    causes  = final["cause_of_death"].nunique()
    print(f"[Transform] D3 雙北主要死因完成，共 {len(final)} 筆，{causes} 種死因，分布：{by_city}")
    return final
