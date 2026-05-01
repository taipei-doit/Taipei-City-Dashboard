"""
transforms/D2_雙北食品抽驗.py
==============================
合併台北市與新北市食品抽驗統計，輸出年度合格率趨勢表。

最終整合策略
------------
  目標：前端雙軸折線圖（年度 pass_rate 並排對比）+ 圓餅圖（不合格原因）

  台北：34筆年度資料（1992~2025）
    - 來源欄位已含不符率與件數，直接轉換
    - fail_reason 從原因別欄位取最大值

  新北：僅保留「有 pass_rate」的資料
    - 季度合格率 → 年均化 → 1筆年度記錄（pass_rate 有值才輸出）
    - 標示合格率、月度批次 → 捨棄（無法接在年度時間軸，不進此表）

  輸出：台北 34筆 + 新北 N筆（目前原始資料只有2025年）
"""

import re
import pandas as pd


def _to_float(val) -> float | None:
    try:
        v = float(str(val).replace('%', '').replace(',', '').strip())
        return None if v != v else v
    except (TypeError, ValueError):
        return None

def _to_int(val) -> int | None:
    f = _to_float(val)
    return int(f) if f is not None else None


# ── 台北市 ───────────────────────────────────────────────────────────────────

_TP_REASON_MAP = {
    "與規定不符件數按原因別_違規標示":            "違規標示",
    "與規定不符件數按原因別_違規廣告":            "違規廣告",
    "與規定不符件數按原因別_食品添加物":          "食品添加物",
    "與規定不符件數按原因別_食品器皿容器包裝檢驗": "包裝器皿",
    "與規定不符件數按原因別_微生物":              "微生物",
    "與規定不符件數按原因別_真菌毒素":            "真菌毒素",
    "與規定不符件數按原因別_黃麴毒素":            "真菌毒素",
    "與規定不符件數按原因別_農藥殘留量":          "農藥殘留",
    "與規定不符件數按原因別_動物用藥殘留":        "動物用藥",
    "與規定不符件數按原因別_化學成分":            "化學成分",
    "與規定不符件數按原因別_成分分析":            "成分分析",
    "與規定不符件數按原因別_異物":                "異物",
    "與規定不符件數按原因別_其他":                "其他",
}

def _top_reason(row, avail_cols):
    best_label, best_val = None, 0
    for col in avail_cols:
        v = _to_int(row.get(col, 0)) or 0
        if v > best_val:
            best_val = v
            best_label = _TP_REASON_MAP.get(col)
    return best_label

def _parse_taipei(df: pd.DataFrame) -> pd.DataFrame:
    print(f"[台北食品抽驗] 原始 {len(df)} 筆")
    df = df.copy()
    df["year"] = [114 - i + 1911 for i in range(len(df))]  # row0=2025，遞減
    avail_cols = [c for c in _TP_REASON_MAP if c in df.columns]
    rows = []
    for _, r in df.iterrows():
        fail_rate = _to_float(r.get("不符規定比率"))
        pass_rate = round(100 - fail_rate, 4) if fail_rate is not None else None
        total     = _to_int(r.get("查驗件數_總計"))
        failed    = _to_int(r.get("與規定不符件數_總計"))
        if fail_rate is None and total and failed and total > 0:
            fail_rate = round(failed / total * 100, 4)
            pass_rate = round(100 - fail_rate, 4)
        rows.append({
            "city_scope": "Taipei", "city": "臺北市",
            "year": int(r["year"]), "period": str(int(r["year"])),
            "total_inspected": total, "total_failed": failed,
            "pass_rate": pass_rate, "fail_rate": fail_rate,
            "fail_reason": _top_reason(r, avail_cols),
            "source_trace": "data.taipei（臺北市食品衛生管理查驗工作，主計處）",
        })
    result = pd.DataFrame(rows)
    print(f"  → {len(result)} 筆（{result['year'].min()}~{result['year'].max()}）")
    return result


# ── 新北市：季度 → 年均，只保留 pass_rate 有值者 ─────────────────────────────

def _parse_ntpc_quarterly(df: pd.DataFrame) -> pd.DataFrame:
    """
    filename 解析年份+季度，percent = 合格率%。
    同年各季取平均 → 1筆年度記錄。
    pass_rate 為 NULL 的直接跳過（不輸出空殼列）。
    """
    print(f"[新北抽驗季度] 原始 {len(df)} 筆")
    rows = []
    for _, r in df.iterrows():
        fn = str(r.get("filename", ""))
        m_y = re.search(r'(\d+)年', fn)
        if not m_y:
            continue
        pass_rate = _to_float(r.get("percent"))
        if pass_rate is None:          # 無合格率就不收
            continue
        year    = int(m_y.group(1)) + 1911
        m_q     = re.search(r'截至(\d+)月底', fn)
        quarter = (int(m_q.group(1)) - 1) // 3 + 1 if m_q else None
        rows.append({"year": year, "quarter": quarter, "pass_rate": pass_rate})

    if not rows:
        print("  → 無有效資料")
        return pd.DataFrame()

    tmp = pd.DataFrame(rows)
    agg = (tmp.groupby("year")
              .agg(pass_rate=("pass_rate", "mean"),
                   n_quarters=("quarter", "count"))
              .round({"pass_rate": 4})
              .reset_index())

    result_rows = []
    for _, a in agg.iterrows():
        year      = int(a["year"])
        pass_rate = round(float(a["pass_rate"]), 4)
        result_rows.append({
            "city_scope": "NewTaipei", "city": "新北市",
            "year": year, "period": str(year),
            "total_inspected": None, "total_failed": None,
            "pass_rate": pass_rate, "fail_rate": round(100 - pass_rate, 4),
            "fail_reason": None,
            "source_trace": f"data.ntpc（市售食品抽驗合格率，衛生局，{int(a['n_quarters'])}季均）",
        })

    result = pd.DataFrame(result_rows)
    print(f"  → 年均化後 {len(result)} 筆（年份：{sorted(result['year'].tolist())}）")
    return result


# ── 主 transform 入口 ─────────────────────────────────────────────────────────

def transform(
    raw: dict[str, pd.DataFrame],
    data_time: str,
    config: dict,
    dataset_configs: dict,
) -> pd.DataFrame:

    tp_df      = _parse_taipei(raw["臺北市食品衛生管理查驗工作"])
    ntpc_df    = _parse_ntpc_quarterly(raw["市售食品抽驗合格率"])
    # 標示合格率、月度批次不進本表（無年度 pass_rate，無法在折線圖對比）

    final = pd.concat([tp_df, ntpc_df], ignore_index=True)
    final["data_time"] = data_time
    final["data_mode"] = "real"

    final = final[[
        "data_time", "city_scope", "city", "year", "period",
        "total_inspected", "total_failed",
        "pass_rate", "fail_rate", "fail_reason",
        "source_trace", "data_mode",
    ]].reset_index(drop=True)

    by_city = final.groupby("city_scope").size().to_dict()
    print(f"[Transform] D2 雙北食品抽驗完成，共 {len(final)} 筆，分布：{by_city}")
    return final