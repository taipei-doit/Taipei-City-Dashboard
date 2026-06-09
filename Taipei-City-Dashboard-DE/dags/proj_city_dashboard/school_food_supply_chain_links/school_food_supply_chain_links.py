from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    """建表（若不存在）。冪等，每次 DAG run 都會跑。"""
    from sqlalchemy.sql import text as sa_text
    from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table

    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        conn.execute(sa_text(sql).execution_options(autocommit=True))


def _school_food_supply_chain_links(**kwargs):
    """雙北學校供餐供應鏈 — 食材登錄平台 OpenAPI 月更新。

    產出供桑基圖（SankeyChart）使用的 link rows：
        source → target (value, layer, city, district)

    其中 layer ∈ {'up-mid', 'mid-down'}：
        up-mid:    上游原料 / 調味料供應商 → 中游供餐業者
        mid-down:  中游供餐業者 → 下游學校
    """
    # === Imports（全部寫在函式內，避免 Airflow 3.x parse 階段 IO） ===
    import io
    import pandas as pd
    import requests
    import os
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # === Config ===
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "city": 'character varying(10) COLLATE pg_catalog."default"',
        "district": 'character varying(20) COLLATE pg_catalog."default"',
        "source_name": 'character varying(200) COLLATE pg_catalog."default"',
        "target_name": 'character varying(200) COLLATE pg_catalog."default"',
        "value": "integer",
        "layer": 'character varying(20) COLLATE pg_catalog."default"',
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    # === API 認證 ===
    # NOTE: 食材登錄平台 OpenAPI 採 email 註冊取碼模式，accesscode 透過 email
    # 食材登錄平台 OpenAPI accesscode（email 註冊取碼）。
    # 透過環境變數 FATRACESCHOOL_ACCESSCODE 注入，避免依賴 Airflow Variable。
    # 若 token 過期需重新向平台申請，更新 docker-compose 的 environment 即可。
    ACCESS_CODE = os.environ.get("FATRACESCHOOL_ACCESSCODE", "")

    # === Helpers ===
    # NOTE: 暫無對應 utils.extract_stage helper 處理 fatraceschool API。
    # 該 API 為 POST + JSON body，需 accesscode 認證，且採「先取下載連結
    # 再下載資料」兩段式流程（下載連結為一次性 timestamped URL，需立即使用），
    # 與既有 helper 模式不同。後續若有更多 DAG 共用此來源，請維護者升級為
    # utils.extract_stage.<helper>。
    BASE_URL = "https://fatraceschool.k12ea.gov.tw/cateringservice/openapi"
    COUNTIES = ["臺北市", "新北市"]
    GRADES = ["國中小", "高中職"]
    DATASET_NAME = "午餐食材及供應商資料集"
    REQ_TIMEOUT = 60
    DOWNLOAD_TIMEOUT = 300  # 單一 CSV 可達 20MB 以上
    MAX_BACK_MONTHS = 6     # 資料延遲約 1-2 個月，scan-back 上限

    def _post_json(endpoint, payload):
        r = requests.post(f"{BASE_URL}/{endpoint}/", json=payload, timeout=REQ_TIMEOUT, verify=False)
        r.raise_for_status()
        return r.json()

    def _find_latest_available_month(county):
        """從本月往前 scan，找最早可用 dataset。資料延遲約 1-2 個月。"""
        today = pd.Timestamp.now(tz="Asia/Taipei").normalize().replace(day=1)
        for back in range(1, MAX_BACK_MONTHS + 1):
            target = today - pd.DateOffset(months=back)
            year, month = target.year, target.month
            info = _post_json("opendatadataset", {
                "accesscode": ACCESS_CODE,
                "year": str(year),
                "month": f"{month:02d}",
                "county": county,
            })
            datasets = info.get("datasetList") or []
            has_target = any(
                d.get("datasetname") == DATASET_NAME
                and d.get("county") == county
                for d in datasets
            )
            if has_target:
                return year, month
        raise RuntimeError(
            f"No '{DATASET_NAME}' available for {county} in last "
            f"{MAX_BACK_MONTHS} months"
        )

    def _fetch_month_county_grade(year, month, county, grade):
        """取單一 (year, month, county, grade) 的資料集 DataFrame。"""
        info = _post_json("opendatadownload", {
            "accesscode": ACCESS_CODE,
            "year": str(year),
            "month": f"{int(month):02d}",
            "county": county,
            "grade": grade,
            "datasetname": DATASET_NAME,
        })
        download_url = info.get("link")
        if not download_url:
            print(f"  [WARN] {county}/{grade} {year}-{month:02d}: no link in response")
            return pd.DataFrame()

        # 一次性連結，立即下載
        f = requests.get(download_url, timeout=DOWNLOAD_TIMEOUT, verify=False)
        f.raise_for_status()
        return pd.read_csv(io.StringIO(f.content.decode("utf-8")))

    def _aggregate_links(raw, county):
        """將原始供餐記錄聚合為桑基 link rows。

        原始欄位（fatraceschool OpenAPI 實測 2026-05）：
            市縣名稱 / 區域名稱 / 學校名稱 / 供餐日期 /
            供餐業者 / 供餐業者統一編號 /
            食材供應商名稱 / 食材供應商統編 / 食材名稱 /
            調味料供應商名稱 / 調味料供應商統編 / 調味料名稱 /
            認證標章 / 認證號碼

        聚合策略（與比賽期 scripts/aggregate-sankey.js 一致）：
            up-mid: 食材供應商 + 調味料供應商 union，groupby(supplier, 供餐業者) 計 row 數
            mid-down: groupby(供餐業者, 區域名稱, 學校名稱) 計 row 數
            value = 該 link 的供餐記錄 row 數（未對日期 dedup，與下游一致）
        """
        rows = []
        if raw.empty:
            return rows

        # 上游 link：食材 + 調味料 兩種供應商 union → 供餐業者
        if "供餐業者" in raw.columns:
            up_parts = []
            if "食材供應商名稱" in raw.columns:
                up_parts.append(
                    raw[["食材供應商名稱", "供餐業者"]]
                    .rename(columns={"食材供應商名稱": "supplier"})
                )
            if "調味料供應商名稱" in raw.columns:
                up_parts.append(
                    raw[["調味料供應商名稱", "供餐業者"]]
                    .rename(columns={"調味料供應商名稱": "supplier"})
                )
            if up_parts:
                up = pd.concat(up_parts, ignore_index=True).dropna(
                    subset=["supplier", "供餐業者"]
                )
                up = up[
                    up["supplier"].astype(str).str.strip().ne("")
                    & up["供餐業者"].astype(str).str.strip().ne("")
                ]
                if not up.empty:
                    agg = (
                        up.groupby(["supplier", "供餐業者"])
                        .size()
                        .reset_index(name="value")
                    )
                    for _, r in agg.iterrows():
                        rows.append({
                            "city": county,
                            "district": None,
                            "source_name": r["supplier"],
                            "target_name": r["供餐業者"],
                            "value": int(r["value"]),
                            "layer": "up-mid",
                        })

        # 下游 link：供餐業者 → 學校（帶區域名稱）
        if {"供餐業者", "學校名稱"}.issubset(raw.columns):
            md = raw.dropna(subset=["供餐業者", "學校名稱"])
            md = md[
                md["供餐業者"].astype(str).str.strip().ne("")
                & md["學校名稱"].astype(str).str.strip().ne("")
            ]
            keys = ["供餐業者", "學校名稱"]
            if "區域名稱" in raw.columns:
                keys.append("區域名稱")
            agg = md.groupby(keys).size().reset_index(name="value")
            for _, r in agg.iterrows():
                rows.append({
                    "city": county,
                    "district": r.get("區域名稱") if "區域名稱" in agg.columns else None,
                    "source_name": r["供餐業者"],
                    "target_name": r["學校名稱"],
                    "value": int(r["value"]),
                    "layer": "mid-down",
                })

        return rows

    # === Extract + Transform ===
    all_rows = []
    for county in COUNTIES:
        try:
            year, month = _find_latest_available_month(county)
            print(f"  [PICK] {county}: latest available month = {year}-{month:02d}")
        except RuntimeError as e:
            print(f"  [FAIL] {county}: {e}")
            continue

        for grade in GRADES:
            try:
                raw = _fetch_month_county_grade(year, month, county, grade)
                rows = _aggregate_links(raw, county)
                all_rows.extend(rows)
                print(f"  [OK] {county}/{grade} {year}-{month:02d}: "
                      f"{len(raw)} raw rows → {len(rows)} links")
            except Exception as e:
                print(f"  [FAIL] {county}/{grade} {year}-{month:02d}: {e}")

    data = pd.DataFrame(
        all_rows, columns=[c for c in SELECT_COLUMNS if c != "data_time"]
    )
    data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")
    data = data[SELECT_COLUMNS]

    # === Load ===
    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)
    save_dataframe_to_postgresql(
        engine,
        data=data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(engine, dag_id, data["data_time"].max())


dag = CommonDag(
    proj_folder="proj_city_dashboard",
    dag_folder="school_food_supply_chain_links",
)
dag.create_dag(etl_func=_school_food_supply_chain_links)
