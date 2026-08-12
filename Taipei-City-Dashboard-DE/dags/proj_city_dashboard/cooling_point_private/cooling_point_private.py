from operators.common_pipeline import CommonDag


def _cooling_point_private(**kwargs):
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
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=9269d8b5-f4fa-44ab-8f2c-5203ba70ebe0"

    # Extract
    response = requests.get(URL, verify=False)
    csv_text = response.content.decode("big5")
    # dtype=str: 市話/分機/手機 是有前導零的電話字串，讓 pandas 自動推斷會變成 float 而掉零
    raw_data = pd.read_csv(StringIO(csv_text), dtype=str)

    # Transform
    data = raw_data.copy()
    data = data.rename(
        columns={
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
            "飲水設施": "water_facility",
            "無障礙座位": "accessible_seat",
            "其他特色及亮點": "features",
            "備註": "note",
        }
    )
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

    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    )
    # select column
    ready_data = gdata[
        [
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
    ]

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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="cooling_point_private")
dag.create_dag(etl_func=_cooling_point_private)
