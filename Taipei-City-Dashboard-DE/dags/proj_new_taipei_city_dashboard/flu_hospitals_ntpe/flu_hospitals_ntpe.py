from airflow import DAG
from operators.common_pipeline import CommonDag
import pandas as pd
import re


# pending 資料來源不全
def _transfer(**kwargs):
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient
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
    # 死亡率
    RATE_RID= "551cd3f4-534a-45cf-976a-359090fb7df6"
    client = NewTaipeiAPIClient(RATE_RID, input_format="json")
    res = client.get_all_data(size=1000)
    df = pd.DataFrame(res)
    df['data_time'] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")


    area_candidates = df['address'].str.slice(3, 6)
    df['district'] = area_candidates.apply(lambda x: x if x.endswith('區') else None)


    df = df.rename(columns={
        "wgs84ax": "lon",
        "wgs84ay": "lat",
    })
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    gdata = add_point_wkbgeometry_column_to_df(
        df, x=df["lon"], y=df["lat"], from_crs=4326
    )
    df = gdata[["name", "tel", "address", "type", 'district', "lon", "lat", "data_time"]]

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=df,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="POINT",
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, df["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="flu_hospitals_ntpe")
dag.create_dag(etl_func=_transfer)
