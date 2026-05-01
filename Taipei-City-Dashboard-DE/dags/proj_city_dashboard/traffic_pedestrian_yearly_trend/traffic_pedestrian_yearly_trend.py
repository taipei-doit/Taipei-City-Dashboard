from airflow import DAG
from operators.common_pipeline import CommonDag


def etl_function(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine, text
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    engine = create_engine(ready_data_db_uri)

    tpe_sql = text("""
        SELECT
            'taipei' AS city,
            year,
            COUNT(*) AS accident_count,
            SUM(death_count) AS death_count,
            SUM(injury_count) AS injury_count
        FROM traffic_pedestrian_accident_taipei
        WHERE year > 0
        GROUP BY year
        ORDER BY year
    """)

    ntpc_sql = text("""
        SELECT
            'ntpc' AS city,
            year,
            COUNT(*) AS accident_count,
            SUM(death_count) AS death_count,
            SUM(injury_count) AS injury_count
        FROM traffic_pedestrian_accident_ntpc
        WHERE year > 0
        GROUP BY year
        ORDER BY year
    """)

    with engine.connect() as conn:
        tpe_df = pd.read_sql(tpe_sql, conn)
        ntpc_df = pd.read_sql(ntpc_sql, conn)

    data = pd.concat([tpe_df, ntpc_df], ignore_index=True)
    print(f"Yearly trend rows: {len(data)}")

    now_str = str(pd.Timestamp.now(tz="Asia/Taipei"))
    data["data_time"] = convert_str_to_time_format(pd.Series([now_str] * len(data)))

    ready_data = data[[
        "data_time", "city", "year",
        "accident_count", "death_count", "injury_count"
    ]]

    # 使用 pandas 寫入（此表無 geometry）
    ready_data.to_sql(
        default_table,
        engine,
        if_exists="replace",
        index=False,
        method="multi",
    )
    print(f"Loaded {len(ready_data)} rows into {default_table}")

    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=str(lasttime_in_data)
    )


dag = CommonDag(
    proj_folder="proj_city_dashboard",
    dag_folder="traffic_pedestrian_yearly_trend"
)
dag.create_dag(etl_func=etl_function)
