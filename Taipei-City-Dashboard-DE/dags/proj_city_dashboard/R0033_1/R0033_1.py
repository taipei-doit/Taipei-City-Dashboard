from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0033_1(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
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
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=4486e759-4159-4208-9832-c32300c4e832"
    ENCODING = "cp950"
    FROM_CRS = 3826
    GEOMETRY_TYPE = "Polygon"

    # Extract
    raw_data = pd.read_csv(URL, encoding=ENCODING)

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(columns={"分隊名稱": "name"})
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["經度"], y=data["緯度"], from_crs=FROM_CRS
    )
    # select columns
    ready_data = gdata[["name", "wkb_geometry"]]

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
    update_lasttime_in_data_to_dataset_info(engine, dag_id)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0033_1")
dag.create_dag(etl_func=_R0033_1)
