from operators.common_pipeline import CommonDag

# 涼適點分成兩個資料集發布，欄位結構相同，合併進同一張表，以 provider 欄位區分。
# 兩邊的「編號」都自己從 1 開始編，併表後 id 不唯一，要辨識單一點位請用 (provider, id)
# 或表上的 ogc_fid。
SOURCES = [
    # (rid, provider)
    # 臺北市涼適點 https://data.taipei/dataset/detail?id=a98a3e0e-a36f-43fa-82f8-b09a3011a47a
    ("ae7e5986-859d-4294-b289-7c1b2e7c23f1", "市府"),
    # 臺北市民間涼適點 https://data.taipei/dataset/detail?id=a1b59e2f-057a-41e2-ae09-482ba5af7d58
    ("9269d8b5-f4fa-44ab-8f2c-5203ba70ebe0", "民間"),
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
    # 兩個資料集對同一欄用了不同標題（民間版把說明括號拿掉），兩種都收；
    # rename 會忽略對不到的 key，多放不會有副作用。
    "飲水設施（例如：飲水機；直飲台；奉茶點等）": "water_facility",
    "飲水設施": "water_facility",
    "無障礙座位": "accessible_seat",
    "其他特色及亮點": "features",
    "備註": "note",
}

READY_COLUMNS = [
    "data_time",
    "provider",
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
    for rid, provider in SOURCES:
        response = requests.get(URL.format(rid=rid), verify=False)
        csv_text = response.content.decode("big5")
        # dtype=str: 市話/分機/手機 有前導零，讓 pandas 自動推斷會變 float64，
        # 寫進 varchar 會多一個 .0 尾巴（972867232 -> 972867232.0）。
        raw_data = pd.read_csv(StringIO(csv_text), dtype=str)
        # 先各自正規化欄名再 concat：兩份 CSV 對「飲水設施」用不同標題，
        # 若等 concat 完才 rename，兩個標題會同時存在而產生兩個 water_facility 欄。
        raw_data = raw_data.rename(columns=COLUMN_MAP)
        raw_data["provider"] = provider
        print(f"Extracted {len(raw_data)} rows from {provider} ({rid}).")
        frames.append(raw_data)

    # Transform
    data = pd.concat(frames, ignore_index=True)
    # 來源為人工維護，經度偶有「緯度，經度」全形逗號並列的填法，取右側經度。
    # mask 全 False 時 expand=True 會回傳 0 欄的 DataFrame，取 [1] 會 KeyError，故先擋掉。
    data["longitude"] = data["longitude"].astype(str).str.replace("，", ",").str.strip()
    mask = data["longitude"].str.contains(",", na=False)
    if mask.any():
        split_coords = data.loc[mask, "longitude"].str.split(",", expand=True)
        data.loc[mask, "longitude"] = split_coords[1].str.strip()
    data["longitude"] = pd.to_numeric(data["longitude"], errors="coerce")
    data["latitude"] = pd.to_numeric(data["latitude"], errors="coerce")
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
