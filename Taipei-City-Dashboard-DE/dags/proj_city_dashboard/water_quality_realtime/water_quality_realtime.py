from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import xml.etree.ElementTree as ET

    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    url = "https://twd.water.gov.taipei/opendata/wqb/wqb.asmx/GetQualityData"
    from_crs = 4326
    geometry_type = "Point"

    response = requests.get(url, proxies=proxies, timeout=60)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    records = []
    for item in root.findall(".//qua_data"):
        records.append({child.tag: (child.text or "").strip() for child in item})

    raw_data = pd.DataFrame(records)
    if raw_data.empty:
        raise ValueError("Water quality API returned no records.")

    data = raw_data.rename(
        columns={
            "update_date": "update_date",
            "update_time": "update_time",
            "qua_id": "station_id",
            "code_name": "station_name",
            "longitude": "lng",
            "latitude": "lat",
            "qua_cntu": "turbidity_ntu",
            "qua_cl": "residual_chlorine_mg_l",
            "qua_ph": "ph",
        }
    )

    data["data_time"] = convert_str_to_time_format(
        data["update_date"].astype(str) + " " + data["update_time"].astype(str)
    )
    for col in ["lng", "lat", "turbidity_ntu", "residual_chlorine_mg_l", "ph"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=["lng", "lat"]).copy()
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=from_crs
    )

    ready_data = gdata[
        [
            "data_time",
            "station_id",
            "station_name",
            "lng",
            "lat",
            "turbidity_ntu",
            "residual_chlorine_mg_l",
            "ph",
            "wkb_geometry",
        ]
    ]

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=geometry_type,
    )

    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(
    proj_folder="proj_city_dashboard", dag_folder="water_quality_realtime"
)
dag.create_dag(etl_func=_transfer)
