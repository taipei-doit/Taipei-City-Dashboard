import os

from airflow import DAG
from operators.common_pipeline import CommonDag

MOA_API_BASE = os.getenv(
    "MOA_API_BASE", "https://data.moa.gov.tw/api/v1"
).rstrip("/")
MOA_API_KEY = os.getenv("MOA_API_KEY", "").strip()

TAIPEI_WHOLESALE_MARKETS = {
    "vegetable_fruit": [
        {"code": "109", "name": "台北一"},
        {"code": "104", "name": "台北二"},
    ],
    "fishery": [
        {"name": "台北"},
        {"name": "三重"},
    ],
    "pork": [
        {"name": "新北市"},
    ],
}


def _get_roc_date_str(dt):
    """Convert datetime to ROC date string, e.g. '115.05.02'."""
    return f"{dt.year - 1911}.{dt.month:02d}.{dt.day:02d}"


def _get_roc_date_compact(dt):
    """Convert datetime to compact ROC date, e.g. '1150502'."""
    return f"{dt.year - 1911}{dt.month:02d}{dt.day:02d}"


def _fetch_vegetable_fruit(session, today):
    """A01: 農產品交易行情 — 蔬果批發."""
    import json

    date_str = _get_roc_date_str(today)
    all_records = []
    for market in TAIPEI_WHOLESALE_MARKETS["vegetable_fruit"]:
        offset = 0
        while True:
            resp = session.get(
                f"{MOA_API_BASE}/AgriProductsTransType/",
                params={
                    "api_key": MOA_API_KEY,
                    "Start_time": date_str,
                    "End_time": date_str,
                    "MarketCode": market["code"],
                    "limit": 2000,
                    "offset": offset,
                },
                timeout=60,
                verify=False,
            )
            resp.raise_for_status()
            data = resp.json()
            batch = [
                r for r in data.get("Data", []) if r.get("CropName") != "休市"
            ]
            for r in batch:
                r["_market_code"] = market["code"]
                r["_market_name"] = market["name"]
            all_records.extend(batch)
            if not data.get("Next") or not batch:
                break
            offset += len(batch)
    return all_records


def _fetch_pork(session, today):
    """毛豬交易行情 — API 資料可能延遲 1~2 天，取最近 3 天內最新."""
    from datetime import timedelta

    valid_dates = {
        _get_roc_date_compact(today - timedelta(days=d))
        for d in range(3)
    }
    resp = session.get(
        f"{MOA_API_BASE}/PorkTransType/",
        params={"api_key": MOA_API_KEY, "limit": 100},
        timeout=60,
        verify=False,
    )
    resp.raise_for_status()
    data = resp.json()
    candidates = [
        r
        for r in data.get("Data", [])
        if r.get("TransDate") in valid_dates
        and r.get("MarketName") in ("新北市",)
    ]
    if not candidates:
        return []
    latest = max(r["TransDate"] for r in candidates)
    return [r for r in candidates if r["TransDate"] == latest]


def _fetch_fishery(session, today):
    """漁產品交易行情."""
    date_compact = _get_roc_date_compact(today)
    target_names = {m["name"] for m in TAIPEI_WHOLESALE_MARKETS["fishery"]}
    all_records = []
    offset = 0
    while True:
        resp = session.get(
            f"{MOA_API_BASE}/FisheryProductsTransType/",
            params={
                "api_key": MOA_API_KEY,
                "limit": 2000,
                "offset": offset,
            },
            timeout=60,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        batch = data.get("Data", [])
        for r in batch:
            if (
                r.get("TransDate") == date_compact
                and r.get("MarketName") in target_names
                and r.get("SeafoodProdName") != "休市"
            ):
                all_records.append(r)
        if not data.get("Next") or not batch:
            break
        offset += len(batch)
    return all_records


def _fetch_poultry(session, today):
    """家禽交易行情 — API 資料延遲 2~3 天，取最近 5 天內最新."""
    from datetime import timedelta

    valid_dates = {
        (today - timedelta(days=d)).strftime("%Y/%m/%d")
        for d in range(5)
    }
    results = []
    endpoints = [
        ("PoultryTransType_BlackFeather", "黑羽土雞"),
        ("PoultryTransType_RedFeather", "紅羽土雞"),
        ("PoultryTransType_BoiledChicken_Eggs", "白肉雞/雞蛋"),
    ]
    for endpoint, label in endpoints:
        resp = session.get(
            f"{MOA_API_BASE}/{endpoint}/",
            params={"api_key": MOA_API_KEY, "limit": 10},
            timeout=60,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        for r in data.get("Data", []):
            if r.get("TransDate") in valid_dates:
                r["_poultry_type"] = label
                results.append(r)
                break
    return results


def _aggregate_to_summary(vf_records, pork_records, fish_records, poultry_records, today):
    """Aggregate raw API records into wholesale_daily_summary rows."""
    import json
    import pandas as pd

    roc_date = _get_roc_date_str(today)
    rows = []

    for market in TAIPEI_WHOLESALE_MARKETS["vegetable_fruit"]:
        items = [r for r in vf_records if r.get("_market_code") == market["code"]]
        if not items:
            continue
        total_qty = sum(r["Trans_Quantity"] for r in items)
        weighted_price = (
            sum(r["Avg_Price"] * r["Trans_Quantity"] for r in items) / total_qty
            if total_qty > 0
            else 0
        )
        top5 = sorted(items, key=lambda x: x["Trans_Quantity"], reverse=True)[:5]
        rows.append({
            "data_date": roc_date,
            "market_code": market["code"],
            "market_name": market["name"],
            "category": "vegetable_fruit",
            "total_items": len(items),
            "total_quantity": round(total_qty, 1),
            "avg_price": round(weighted_price, 2),
            "top_items": json.dumps(
                [{"name": r["CropName"], "qty": r["Trans_Quantity"], "price": r["Avg_Price"]}
                 for r in top5],
                ensure_ascii=False,
            ),
        })

    for r in pork_records:
        rows.append({
            "data_date": roc_date,
            "market_code": r["MarketName"],
            "market_name": r["MarketName"] + "肉品市場",
            "category": "pork",
            "total_items": 1,
            "total_quantity": float(r.get("TransNum_Total", 0)),
            "avg_price": float(r.get("TransNum_AvgPrice", 0)),
            "top_items": json.dumps(
                [{"name": "毛豬", "qty": r.get("TransNum_Total", 0),
                  "price": r.get("TransNum_AvgPrice", 0)}],
                ensure_ascii=False,
            ),
        })

    fish_by_market = {}
    for r in fish_records:
        mkt = r["MarketName"]
        fish_by_market.setdefault(mkt, []).append(r)
    for mkt, items in fish_by_market.items():
        total_qty = sum(r["Trans_Quantity"] for r in items)
        weighted_price = (
            sum(r["Avg_Price"] * r["Trans_Quantity"] for r in items) / total_qty
            if total_qty > 0
            else 0
        )
        top5 = sorted(items, key=lambda x: x["Trans_Quantity"], reverse=True)[:5]
        rows.append({
            "data_date": roc_date,
            "market_code": mkt,
            "market_name": mkt + "魚市",
            "category": "fishery",
            "total_items": len(items),
            "total_quantity": round(total_qty, 1),
            "avg_price": round(weighted_price, 2),
            "top_items": json.dumps(
                [{"name": r["SeafoodProdName"], "qty": r["Trans_Quantity"],
                  "price": r["Avg_Price"]} for r in top5],
                ensure_ascii=False,
            ),
        })

    if poultry_records:
        rows.append({
            "data_date": roc_date,
            "market_code": "NATIONAL",
            "market_name": "全國家禽行情",
            "category": "poultry",
            "total_items": len(poultry_records),
            "total_quantity": 0,
            "avg_price": 0,
            "top_items": json.dumps(
                [{"name": r.get("_poultry_type", ""), "price": r.get("BlackFeather_S_M", "")}
                 for r in poultry_records[:5]],
                ensure_ascii=False,
            ),
        })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _fetch_trust_data_from_db(engine):
    """Read traceability + CAS data from DB tables (populated by independent DAGs)."""
    from sqlalchemy.sql import text as sa_text

    with engine.connect() as conn:
        trace_rows = conn.execute(
            sa_text("SELECT sampling_location, inspect_result FROM traceability_inspection")
        ).fetchall()
        trace_data = [
            {"SamplingLocation": row[0], "InspectResult": row[1]}
            for row in trace_rows
        ]

        cas_rows = conn.execute(
            sa_text("SELECT material_name FROM cas_product")
        ).fetchall()
        cas_data = [{"Material_Name": row[0]} for row in cas_rows]

    return trace_data, cas_data


def _compute_trust_scores(trace_data, cas_data):
    """
    Trust Score (0~100) = 0.6 * traceability_rate + 0.3 * cas_coverage + 0.1 * base

    - traceability_rate: % of 合格 in 產銷履歷 samples from Taipei area
    - cas_coverage: presence of CAS-certified products in meat/poultry supply
    - base: baseline score (all markets get 50 if supply is active)
    """
    import json

    taipei_traces = [
        r for r in trace_data
        if any(k in r.get("SamplingLocation", "") for k in ("臺北", "台北", "新北"))
    ]
    total_traces = len(taipei_traces) if taipei_traces else 1
    pass_traces = len([r for r in taipei_traces if r.get("InspectResult") == "合格"])
    traceability_rate = (pass_traces / total_traces) * 100

    cas_meat_count = len([r for r in cas_data if r.get("Material_Name") == "肉品"])
    cas_coverage = min(cas_meat_count / 10.0, 1.0) * 100

    return {
        "traceability_rate": round(traceability_rate, 1),
        "traceability_samples": total_traces,
        "traceability_passed": pass_traces,
        "cas_coverage": round(cas_coverage, 1),
        "cas_products": cas_meat_count,
    }


def _update_supply_status(engine, today_roc, trust_info):
    """Join wholesale_daily_summary + market_supply_chain → market_supply_status."""
    import json
    from sqlalchemy.sql import text as sa_text

    base_score = (
        0.6 * trust_info["traceability_rate"]
        + 0.3 * trust_info["cas_coverage"]
        + 0.1 * 50
    )
    base_score = round(min(base_score, 100), 1)
    trust_json = json.dumps(trust_info, ensure_ascii=False)

    sql = sa_text(f"""
        INSERT INTO market_supply_status
            (retail_table, retail_name, retail_district,
             supply_active, supply_categories, total_items, total_quantity,
             top_items, trust_score, trust_detail, status_text, updated_at)
        SELECT
            sc.retail_table,
            sc.retail_name,
            sc.retail_district,
            COALESCE(bool_or(ws.total_items > 0), false) AS supply_active,
            COALESCE(array_agg(DISTINCT sc.wholesale_category)
                     FILTER (WHERE ws.total_items > 0), ARRAY[]::text[]) AS supply_categories,
            COALESCE(SUM(ws.total_items), 0)::integer AS total_items,
            COALESCE(SUM(ws.total_quantity), 0) AS total_quantity,
            (SELECT jsonb_agg(item)
             FROM (
                SELECT item
                FROM wholesale_daily_summary wds2,
                     jsonb_array_elements(wds2.top_items) AS item
                WHERE wds2.data_date = :today_roc
                  AND wds2.market_code = ANY(
                      SELECT sc2.wholesale_code FROM market_supply_chain sc2
                      WHERE sc2.retail_table = sc.retail_table
                        AND sc2.retail_name = sc.retail_name
                  )
                ORDER BY (item->>'qty')::float DESC
                LIMIT 5
             ) sub
            ) AS top_items,
            CASE WHEN bool_or(ws.total_items > 0)
                 THEN :base_score ELSE 0 END AS trust_score,
            :trust_json ::jsonb AS trust_detail,
            CASE WHEN bool_or(ws.total_items > 0)
                 THEN '今日新鮮物資已由批發市場供應'
                 ELSE '今日批發市場休市' END AS status_text,
            NOW() AS updated_at
        FROM market_supply_chain sc
        LEFT JOIN wholesale_daily_summary ws
            ON ws.market_code = sc.wholesale_code
           AND ws.category = sc.wholesale_category
           AND ws.data_date = :today_roc
        GROUP BY sc.retail_table, sc.retail_name, sc.retail_district
        ON CONFLICT (retail_table, retail_name) DO UPDATE SET
            supply_active = EXCLUDED.supply_active,
            supply_categories = EXCLUDED.supply_categories,
            total_items = EXCLUDED.total_items,
            total_quantity = EXCLUDED.total_quantity,
            top_items = EXCLUDED.top_items,
            trust_score = EXCLUDED.trust_score,
            trust_detail = EXCLUDED.trust_detail,
            status_text = EXCLUDED.status_text,
            updated_at = EXCLUDED.updated_at;
    """)

    with engine.begin() as conn:
        conn.execute(sql, {"today_roc": today_roc, "base_score": base_score, "trust_json": trust_json})


def _transfer(**kwargs):
    import urllib3
    import pandas as pd
    import requests
    from datetime import datetime
    from sqlalchemy import create_engine
    from sqlalchemy.sql import text as sa_text
    from utils.get_time import get_tpe_now_time_str

    if not MOA_API_KEY:
        raise ValueError(
            "MOA_API_KEY is not set. Configure MOA_API_KEY (and optionally MOA_API_BASE); "
            "see docker/.env.template."
        )

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")

    engine = create_engine(ready_data_db_uri)
    session = requests.Session()
    today = datetime.now()
    today_roc = _get_roc_date_str(today)

    # --- Step 1: Fetch all wholesale data ---
    vf = _fetch_vegetable_fruit(session, today)
    pork = _fetch_pork(session, today)
    fish = _fetch_fishery(session, today)
    poultry = _fetch_poultry(session, today)

    # --- Step 2: Aggregate and save ---
    summary_df = _aggregate_to_summary(vf, pork, fish, poultry, today)

    with engine.begin() as conn:
        conn.execute(
            sa_text("DELETE FROM wholesale_daily_summary WHERE data_date = :d"),
            {"d": today_roc},
        )
        if not summary_df.empty:
            summary_df["fetched_at"] = get_tpe_now_time_str(is_with_tz=True)
            summary_df.to_sql(
                "wholesale_daily_summary",
                conn,
                if_exists="append",
                index=False,
                schema="public",
            )

    # --- Step 3: Fetch trust data and compute scores ---
    trace_data, cas_data = _fetch_trust_data_from_db(engine)
    trust_info = _compute_trust_scores(trace_data, cas_data)

    # --- Step 4: Update supply status ---
    _update_supply_status(engine, today_roc, trust_info)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="wholesale_supply_chain")
dag.create_dag(etl_func=_transfer)
