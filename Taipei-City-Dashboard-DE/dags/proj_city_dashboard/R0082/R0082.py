from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0082(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_file_last_modified_time
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # Comfig
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=a6546ae5-8d02-4b9c-8b4a-b149228c8cf3"
    ENCODING = "utf-8"
    PAGE_ID = "6b05d331-4eb8-4f0f-a95c-f619511839e7"
    FROM_CRS = 3826
    GEOMETRY_TYPE = "Point"

    # Extract
    raw_data = pd.read_csv(URL, encoding=ENCODING)
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "Name": "name",
            "閘門類別": "gate_type",
            "閥門類別": "valve_type",
            "尺寸": "size",
            "數量": "quantity",
            "河系名稱": "river",
            "行政區域": "dist",
            "管理單位別": "management_unit",
            "X坐標": "twd97_lng",
            "Y坐標": "twd97_lat",
        }
    )
    # add columns
    is_gate = data["gate_type"].notnull()
    is_valve = data["valve_type"].notnull()
    is_gate_and_valve = is_gate & is_valve
    data["type"] = None
    data.loc[is_gate, "type"] = "閘門"
    data.loc[is_valve, "type"] = "閥門"
    data.loc[is_gate_and_valve, "type"] = "閘門及閥門"
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["twd97_lng"], data["twd97_lat"], from_crs=FROM_CRS
    )
    # select columns
    ready_data = gdata[
        [
            "data_time",
            "name",
            "river",
            "dist",
            "management_unit",
            "type",
            "size",
            "quantity",
            "lng",
            "lat",
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
        geometry_type=GEOMETRY_TYPE,
    )
    lasttime_in_data = gdata["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0082")
dag.create_dag(etl_func=_R0082)
