from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import TaipeiTravelAPIClient
    from utils.load_stage import (
        save_dataframe_to_postgresql,
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
    # Load
    PATH = "zh-tw/Attractions/All"
    client = TaipeiTravelAPIClient(PATH, input_format="json")
    res = client.get_all_data()
    raw_data = pd.DataFrame(res)
    df = raw_data.copy() 
    # 取得第一個類別的名稱
    df['type'] = df['category'].apply(lambda x: x[0]['name'] if isinstance(x, list) and len(x) > 0 else None)

    gdata = add_point_wkbgeometry_column_to_df(
            data, x=data["elong"], y=data["nlat"], from_crs=4326
        )
        # select column
    gdata = gdata.rename(
        columns={
            "elong": "longitude",
            "nlat": "latitude"
        }
    )
    data = gdata[["name", "type", "introduction", "address", "distric", "tel", "longitude", "latitude", "wkb_geometry"]]
    data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")

    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, data["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="tourist_attractions")
dag.create_dag(etl_func=_transfer)
