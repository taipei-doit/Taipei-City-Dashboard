import logging
from airflow import DAG
from operators.common_pipeline import CommonDag


def _cooling_point(**kwargs):
    import requests
    import pandas as pd
    from io import StringIO
    from sqlalchemy import create_engine

    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str
    from utils.transform_address import (
        clean_data,
        get_addr_xy_parallel,
        main_process,
        save_data,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    geometry_type = "Point"
    FROM_CRS = 4326
    URL = 'https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=ae7e5986-859d-4294-b289-7c1b2e7c23f1'
    response = requests.get(URL, verify=False)
    # 讀取 CSV
    raw_data = pd.read_csv(StringIO(response.text), encoding='big5')
    logging.info(f"Raw data columns: {raw_data.columns.tolist()}")
    logging.info(f"Raw data sample:\n{raw_data.head()}")
    # Transform
    data = raw_data.copy()
    # Transform: rename fields to standardized columns
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
            "飲水設施（例如：飲水機；直飲台；奉茶點等）": "water_facility",
            "無障礙座位": "accessible_seat",
            "其他特色及亮點": "features",
            "備註": "note",
        }
    )

    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    )
    # select column
    ready_data = gdata[["data_time", "id", "location_type", "name", "area", "address", "longitude", "latitude", "localcall", "ext", "mobile", "contact_other", "open_time", "fan", "aircon", "toilet", "seat", "water_facility", "accessible_seat", "features", "note", "wkb_geometry"]]

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
