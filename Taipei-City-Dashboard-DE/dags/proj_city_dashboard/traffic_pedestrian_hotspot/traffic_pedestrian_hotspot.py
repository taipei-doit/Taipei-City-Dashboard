from airflow import DAG
from operators.common_pipeline import CommonDag


def etl_function(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine, text
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    engine = create_engine(ready_data_db_uri)
    CURRENT_YEAR = pd.Timestamp.now().year
    THREE_YEARS_AGO = CURRENT_YEAR - 3

    # 聚合策略：座標四捨五入到小數點後 3 位（約 100 公尺精度）
    tpe_sql = text(f"""
        SELECT
            'taipei' AS city,
            ROUND(lng::numeric, 3)::float AS center_lng,
            ROUND(lat::numeric, 3)::float AS center_lat,
            COUNT(*) AS accident_count,
            SUM(death_count) AS death_count,
            SUM(injury_count) AS injury_count,
            MODE() WITHIN GROUP (ORDER BY cause_name) AS top_cause,
            MODE() WITHIN GROUP (ORDER BY hour) AS top_hour
        FROM traffic_pedestrian_accident_taipei
        WHERE year >= {THREE_YEARS_AGO}
            AND lng IS NOT NULL AND lat IS NOT NULL
        GROUP BY center_lng, center_lat
        HAVING COUNT(*) >= 2
        ORDER BY accident_count DESC
        LIMIT 500
    """)

    ntpc_sql = text(f"""
        SELECT
            'ntpc' AS city,
            ROUND(lng::numeric, 3)::float AS center_lng,
            ROUND(lat::numeric, 3)::float AS center_lat,
            COUNT(*) AS accident_count,
            SUM(death_count) AS death_count,
            SUM(injury_count) AS injury_count,
            MODE() WITHIN GROUP (ORDER BY cause_name) AS top_cause,
            MODE() WITHIN GROUP (ORDER BY hour) AS top_hour
        FROM traffic_pedestrian_accident_ntpc
        WHERE year >= {THREE_YEARS_AGO}
            AND lng IS NOT NULL AND lat IS NOT NULL
        GROUP BY center_lng, center_lat
        HAVING COUNT(*) >= 2
        ORDER BY accident_count DESC
        LIMIT 500
    """)

    with engine.connect() as conn:
        tpe_df = pd.read_sql(tpe_sql, conn)
        ntpc_df = pd.read_sql(ntpc_sql, conn)

    data = pd.concat([tpe_df, ntpc_df], ignore_index=True)
    print(f"Hotspot rows: {len(data)}")

    data["near_location"] = ""
    data["h3_index"] = ""

    now_str = str(pd.Timestamp.now(tz="Asia/Taipei"))
    data["data_time"] = convert_str_to_time_format(pd.Series([now_str] * len(data)))

    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["center_lng"], y=data["center_lat"], from_crs=4326
    )

    ready_data = gdata[[
        "data_time", "city", "h3_index", "center_lng", "center_lat",
        "accident_count", "death_count", "injury_count",
        "top_cause", "top_hour", "near_location", "wkb_geometry"
    ]]

    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point",
    )
    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=str(lasttime_in_data)
    )


dag = CommonDag(
    proj_folder="proj_city_dashboard",
    dag_folder="traffic_pedestrian_hotspot"
)
dag.create_dag(etl_func=etl_function)
