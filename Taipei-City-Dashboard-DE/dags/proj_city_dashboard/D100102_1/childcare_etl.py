from airflow import DAG
from operators.common_pipeline import CommonDag

def childcare_etl(rid, page_id, **kwargs):
    """
    只入庫指定欄位：
      ['type', 'name', 'address', 'phone', 'data_time', 'town', 'wkb_geometry']
    其他來源欄位一律忽略；缺欄位自動補 None，避免 KeyError。
    """
    import pandas as pd
    from sqlalchemy import create_engine

    # === utils ===
    from utils.extract_stage import (
        get_data_taipei_api,
        get_data_taipei_file_last_modified_time,
    )
    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_address import (
        clean_data,
        main_process,
        save_data,
        get_addr_xy_parallel,
    )
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # ===== Config from kwargs =====
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos", {}) or {}
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    from_crs = 4326

    # ===== Extract =====
    raw = get_data_taipei_api(rid)
    raw_df = pd.DataFrame(raw)
    # 動態取得 data.taipei 頁面右側「更新時間」作為資料時間
    raw_df["data_time"] = get_data_taipei_file_last_modified_time(page_id)

    # ===== Transform =====
    # 來源→目標欄位對應（只要這四個）
    name_dict = {
        "機構類型": "type",
        "機構名稱": "name",
        "地址": "address",
        "電話": "phone",
    }

    # 1) 先移除常見雜項欄位 & 問題欄位（例如中文「序號」）
    drop_candidates = ["_id", "_importdate", "序號"]
    keep_cols = [c for c in raw_df.columns if c not in drop_candidates]
    df = raw_df[keep_cols].copy()

    # 2) 重新命名（只針對指定欄位）
    df = df.rename(columns=name_dict)

    # 3) 只保留我們要的欄位（若缺則後面補 None）
    desired = ["type", "name", "address", "phone", "data_time"]
    exists = [c for c in desired if c in df.columns]
    df = df[exists].copy()
    # 把缺的欄位補上（統一欄位集合）
    for col in desired:
        if col not in df.columns:
            df[col] = None

    # 4) 地址清理與標準化（若 address 皆為 None 會自動跳過）
    if df["address"].notna().any():
        addr = df["address"].fillna("")
        addr_cleaned = clean_data(addr)
        standard_addr_list = main_process(addr_cleaned)
        _, std_addr = save_data(addr, addr_cleaned, standard_addr_list)
        df["address"] = std_addr.astype(str).str.replace(r"\s+$", "", regex=True).str.replace("\n", "").str.strip()
    else:
        df["address"] = None

    # 5) 行政區萃取（優先抓「..區」，否則保底取第 4~6 字）
    if df["address"].notna().any():
        town_extracted = df["address"].str.extract(r"(..區)")[0]
        df["town"] = town_extracted.where(town_extracted.notna(), df["address"].str[3:6])
    else:
        df["town"] = None

    # 6) 時間轉換（tz-aware → 建議對應 PG timestamptz）
    df["data_time"] = convert_str_to_time_format(df["data_time"])

    # 7) 取得經緯度（地址可能有 None，get_addr_xy_parallel 應能處理空字串/None）
    if df["address"].notna().any():
        lng, lat = get_addr_xy_parallel(df["address"], sleep_time=0.5)
        df["lng"], df["lat"] = lng, lat
    else:
        df["lng"], df["lat"] = None, None

    # 8) 幾何欄位（WKB, SRID=4326）
    gdf = add_point_wkbgeometry_column_to_df(df, x=df["lng"], y=df["lat"], from_crs=from_crs)

    # 9) 僅留最終入庫欄位（白名單）
    final_cols = ["type", "name", "address", "phone", "data_time", "town", "wkb_geometry"]
    for col in final_cols:
        if col not in gdf.columns:
            gdf[col] = None
    ready = gdf[final_cols].copy()

    # ===== Load =====
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point",
    )

    # ===== Update dataset_info.lasttime_in_data =====
    lasttime_in_data = ready["data_time"].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )

