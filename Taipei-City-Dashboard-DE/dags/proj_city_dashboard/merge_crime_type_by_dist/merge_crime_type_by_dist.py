from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from sqlalchemy.sql import text as sa_text
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    GEOMETRY_TYPE = "Point"
    # Extract
    sql = """
            select * FROM public.patrol_motorcycle_theft
            union all
            select * FROM public.patrol_residential_burglary
            union all
            select * FROM public.patrol_car_theft
            union all
            select * FROM public.patrol_random_robber
            union all
            select * FROM public.patrol_random_snatch
    """
    engine = create_engine(ready_data_db_uri)
    conn = engine.connect()
    df = pd.read_sql(
        sa_text(sql),
        conn
    )
    # 取地區
    df['dist'] = df['address'].str.extract(r'(.{2,3}區)')
    df["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    df = df[["case_id", "type", "date", "time", "location", "address", "wkb_geometry", "begin_when", "epoch_time", "dist",'data_time']]
    # Load
    ready_data = df.copy()

    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )
    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)



dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="merge_crime_type_by_dist")
dag.create_dag(etl_func=_transfer)
