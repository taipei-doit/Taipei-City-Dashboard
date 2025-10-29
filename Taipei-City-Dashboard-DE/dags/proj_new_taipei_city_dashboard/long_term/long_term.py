from airflow import DAG
from operators.common_pipeline import CommonDag

def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.get_time import get_tpe_now_time_str
    import re

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # Extract
    RID = "a0323809-1c7b-42f3-8dea-2b14f40118f7"  
    client = NewTaipeiAPIClient(RID, input_format="json")
    res = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Transform - 欄位重命名
    raw_data = raw_data.rename(columns={
        "seqno": "place_id",
        "hosp_name": "place_name",
        "tel": "tel",
        "extension": "extension",
        "mobiletelephone": "mobile_phone",
        "hosp_addr": "address",
        "service_area": "service_area",
        "service_item": "service_item",
        "contact_person": "contact_person",
        "wgs84ax": "lng",
        "wgs84ay": "lat"
    })

    # 將空字串轉換為 NaN，再轉為 float
    raw_data["lng"] = pd.to_numeric(raw_data["lng"], errors="coerce")
    raw_data["lat"] = pd.to_numeric(raw_data["lat"], errors="coerce")


    # 擷取 city 與 zone
    def extract_city_zone(addr: str):
        match = re.match(r"(..[市縣])(..區)", addr)
        if match:
            return match.group(1), match.group(2)
        return None, None

    raw_data["city"], raw_data["zone"] = zip(*raw_data["address"].map(extract_city_zone))

    # 加入 wkb_geometry 欄位
    gdata = add_point_wkbgeometry_column_to_df(
        raw_data,
        raw_data["lng"],
        raw_data["lat"],
        from_crs=4326
    )

    ready_data = gdata[[
        "place_id", "place_name", "tel", "extension", "mobile_phone",
        "address", "city", "zone", "service_area", "service_item", "contact_person",
        "lng", "lat", "wkb_geometry", "data_time"
    ]]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point"
    )
    update_lasttime_in_data_to_dataset_info(engine, dag_id, ready_data["data_time"].max())

# 建立 DAG
dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="long_term"
)
dag.create_dag(etl_func=_transfer)
