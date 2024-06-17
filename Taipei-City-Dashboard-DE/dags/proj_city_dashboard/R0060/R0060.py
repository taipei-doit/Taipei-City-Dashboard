from airflow import DAG
from operators.common_pipeline import CommonDag


def _filter_out_existing_license(raw, default_table, engine):
    import pandas as pd

    # transform raw data to match existing data
    raw = raw.rename(columns={"工程金額": "工程造價"})
    raw["建築地點_點位"] = raw["建築地點"].str.split(" ").str[0]

    # read existing data
    existing_data = pd.read_sql(f"SELECT * FROM {default_table}", engine)

    # filter out existing data
    compare_cols = [
        "執照年度",
        "執照號碼",
        "發照日期",
        "設計人",
        "監造人",
        "建造類別",
        "構造種類",
        "使用分區",
        "棟數",
        "地上層數",
        "地下層數",
        "戶數",
        "騎樓基地面積",
        "其他基地面積",
        "建築面積",
        "工程造價",
        "地段地號",
    ]
    join_data = raw.merge(
        existing_data[compare_cols], on=compare_cols, how="outer", indicator=True
    )
    is_new_data = join_data["_merge"] == "left_only"
    new_data = join_data.loc[is_new_data]
    return new_data.drop(columns=["_merge", "建築地點_點位"])


def _R0060(**kwargs):
    from proj_city_dashboard.R0059.R0059 import (
        extarct_license_from_xml,
        transform_license,
    )
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_file_last_modified_time
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=07b57a4e-5ac8-471b-a5cd-4cb8bb4e5c59"
    filename = f"{dag_id}.xml"
    PAGE_ID = "c876ff02-af2e-4eb8-bd33-d444f5052733"
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # Extract
    raw_data = extarct_license_from_xml(filename, URL)

    # Transform
    engine = create_engine(ready_data_db_uri)
    incremental_data = _filter_out_existing_license(raw_data, default_table, engine)
    if incremental_data.empty:
        print("No new data to save.")
    else:
        ready_data = transform_license(incremental_data, FROM_CRS)
        # Load
        save_geodataframe_to_postgresql(
            engine,
            gdata=ready_data,
            load_behavior=load_behavior,
            default_table=default_table,
            history_table=None,
            geometry_type=GEOMETRY_TYPE,
        )

    # Update dataset_info whether there is new data or not
    lasttime_in_data = get_data_taipei_file_last_modified_time(PAGE_ID)
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0060")
dag.create_dag(etl_func=_R0060)
