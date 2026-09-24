from airflow import DAG  # noqa: F401
from operators.common_pipeline import CommonDag

# 上面那個 DAG import 看起來沒用到，但不能刪：Airflow 的 DagBag 在 safe mode
# （AIRFLOW__CORE__DAG_DISCOVERY_SAFE_MODE，預設 True）下，只會 parse 內容同時
# 含 "dag" 與 "airflow" 兩個字串的 .py，不符合的直接跳過，而且不會列進 import
# errors —— DAG 會安靜地整個消失。本 repo 其餘所有 DAG 檔都含這個字串。

# 涼適點資料來源包含：
# 1. 臺北市公有涼適點（中文欄名，沿用編號 1..N）
# 2. 臺北市民間合作涼適點（中文欄名，編號撞號故不沿用）
# 3. 環境部 coolmap 納入之本市合作涼適點（英文欄名、0/1 旗標，代碼編號故不沿用）
SOURCES = [
    # (rid, 來源, 是否沿用來源「編號」, 格式類型)
    # 臺北市涼適點 https://data.taipei/dataset/detail?id=a98a3e0e-a36f-43fa-82f8-b09a3011a47a
    ("ae7e5986-859d-4294-b289-7c1b2e7c23f1", "市府", True, "default"),
    # 民間合作涼適點。編號同樣從 1 開始，與市府撞號，故不沿用。
    # https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=1894ffb6-abea-42e5-9f87-665593376df4
    ("1894ffb6-abea-42e5-9f87-665593376df4", "民間", False, "default"),
    # 環境部coolmap納入之本市合作涼適點。
    # https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=7f404ef2-ac27-45cc-a300-cfcef3c69394
    ("7f404ef2-ac27-45cc-a300-cfcef3c69394", "環境部coolmap", False, "coolmap"),
]

COLUMN_MAP = {
    "編號": "id",
    "設施地點（戶外或室內）": "location_type",
    "名稱": "name",
    "行政區": "area",
    "地址": "address",
    "經度": "longitude",
    "緯度": "latitude",
    "市話": "localcall",
    "分機": "ext",
    "手機": "mobile",
    "其他聯絡方式": "contact_other",
    "開放時間": "open_time",
    "電風扇": "fan",
    "冷氣": "aircon",
    "廁所": "toilet",
    "座位": "seat",
    # 兩份 CSV 對同一欄用了不同標題（民間版把說明括號拿掉），一律收斂成 water_facility。
    # rename 會忽略對不到的 key，兩種都列著不會有副作用。
    "飲水設施（例如：飲水機；直飲台；奉茶點等）": "water_facility",
    "飲水設施": "water_facility",
    "無障礙座位": "accessible_seat",
    "其他特色及亮點": "features",
    "備註": "note",
}

READY_COLUMNS = [
    "data_time",
    "id",
    "location_type",
    "name",
    "area",
    "address",
    "longitude",
    "latitude",
    "localcall",
    "ext",
    "mobile",
    "contact_other",
    "open_time",
    "fan",
    "aircon",
    "toilet",
    "seat",
    "water_facility",
    "accessible_seat",
    "features",
    "note",
    "wkb_geometry",
]


def _cooling_point(**kwargs):
    from io import StringIO

    import pandas as pd
    import requests
    from sqlalchemy import create_engine

    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    def _transform_coolmap(df):
        district_clean = df["district"].astype(str).str.strip()

        def format_address(row):
            addr = str(row["address"]).strip() if pd.notna(row["address"]) else ""
            dist = str(row["district"]).strip() if pd.notna(row["district"]) else ""
            if addr.startswith(("臺北市", "台北市")):
                return addr
            if dist and addr.startswith(dist):
                return f"臺北市{addr}"
            return f"臺北市{dist}{addr}" if dist else f"臺北市{addr}"

        phone_series = df["phone"].astype(str).str.strip()
        has_hash = phone_series.str.contains("#", na=False)
        localcall = phone_series.copy()
        ext = pd.Series(pd.NA, index=df.index, dtype="string")
        if has_hash.any():
            split_phone = phone_series[has_hash].str.split("#", expand=True)
            localcall.loc[has_hash] = split_phone[0].str.strip()
            ext.loc[has_hash] = split_phone[1].str.strip()
        localcall = localcall.replace({"nan": pd.NA, "": pd.NA})

        yn = lambda col: df[col].map({1: "Y", 0: "N"}).fillna(pd.NA)
        location_type = df["isoutdoor"].map({1: "戶外", 0: "室內"}).fillna("室內")

        return pd.DataFrame({
            "id": pd.Series(pd.NA, index=df.index, dtype="Int64"),
            "location_type": location_type,
            "name": df["placename"].astype(str).str.strip(),
            "area": district_clean,
            "address": df.apply(format_address, axis=1),
            "longitude": df["longitude"],
            "latitude": df["latitude"],
            "localcall": localcall,
            "ext": ext,
            "mobile": pd.NA,
            "contact_other": pd.NA,
            "open_time": df["openinghours"].fillna(pd.NA).replace({"nan": pd.NA, "": pd.NA}),
            "fan": pd.NA,
            "aircon": yn("airconditioning"),
            "toilet": yn("restroom"),
            "seat": yn("seats"),
            "water_facility": yn("waterdispenser"),
            "accessible_seat": yn("isaccessible"),
            "features": df["coolingtype"].astype(str).str.strip(),
            "note": pd.NA,
        })

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    geometry_type = "Point"
    FROM_CRS = 4326
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid={rid}"

    # Extract
    frames = []
    for rid, source, keep_id, schema_type in SOURCES:
        response = requests.get(URL.format(rid=rid), verify=False)
        csv_text = response.content.decode("big5")
        raw_data = pd.read_csv(StringIO(csv_text))
        if schema_type == "coolmap":
            processed_data = _transform_coolmap(raw_data)
        else:
            # 先各自正規化欄名再 concat：兩份 CSV 的「飲水設施」標題不同，
            # 若等 concat 完才 rename，兩個標題會同時存在而產生兩個 water_facility 欄。
            processed_data = raw_data.rename(columns=COLUMN_MAP)
            if not keep_id:
                processed_data["id"] = pd.NA
        print(f"Extracted {len(processed_data)} rows from {source} ({rid}).")
        frames.append(processed_data)

    # Transform
    data = pd.concat(frames, ignore_index=True)
    # Int64（可空整數）：民間與環境部那份 id 是 NA，若讓 pandas 退回 float64，
    # 既有的 720 筆會從 1 變成 1.0 寫進表裡。
    data["id"] = data["id"].astype("Int64")
    # 來源為人工維護，經度偶有「緯度，經度」全形逗號並列的填法，取右側經度。
    # mask 全 False 時 expand=True 會回傳 0 欄的 DataFrame，取 [1] 會 KeyError，故先擋掉。
    data["longitude"] = data["longitude"].astype(str).str.replace("，", ",").str.strip()
    mask = data["longitude"].str.contains(",", na=False)
    if mask.any():
        split_coords = data.loc[mask, "longitude"].str.split(",", expand=True)
        data.loc[mask, "longitude"] = split_coords[1].str.strip()
    data["longitude"] = pd.to_numeric(data["longitude"], errors="coerce")
    data["latitude"] = pd.to_numeric(data["latitude"], errors="coerce")
    data["area"] = data["area"].astype(str).str.strip()
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    no_coord = int(data["longitude"].isna().sum() + data["latitude"].isna().sum())
    if no_coord:
        # 來源目前有少數列填成雙座標或度分秒，轉不了數字就沒有點位，記一筆方便追。
        print(f"WARNING: {no_coord} coordinate value(s) could not be parsed, geometry will be NULL.")

    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    )
    # select column
    ready_data = gdata[READY_COLUMNS]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=geometry_type,
    )
    lasttime_in_data = get_tpe_now_time_str()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="cooling_point")
dag.create_dag(etl_func=_cooling_point)
