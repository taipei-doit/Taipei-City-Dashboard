from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050601(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.extract_stage import get_data_taipei_api
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID = "047024e1-b7a2-4b74-b6ac-e9c2a0072593"

    # Extract
    raw_list = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(raw_list)
    raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "年度": "year",
            "住商部門排放量_萬公噸": "residential_commercial_sector_emission_10k_ton",
            "住商部門占比_％": "residential_commercial_sector_percentage",
            "運輸部門排放量_萬公噸": "transportation_sector_emission_10k_ton",
            "運輸部門占比_％": "transportation_sector_percentage",
            "廢棄物部門排放量_萬公噸": "waste_sector_emission_10k_ton",
            "廢棄物部門占比_％": "waste_sector_percentage",
            "工業部門排放量_萬公噸": "industrial_sector_emission_10k_ton",
            "工業部門占比_％": "industrial_sector_percentage",
            "農業部門排放量_萬公噸": "agricultural_sector_emission_10k_ton",
            "農業部門占比_％": "agricultural_sector_percentage",
            "森林部門排放量_萬公噸": "forest_sector_emission_10k_ton",
            "森林部門占比_％": "forest_sector_percentage",
            "總排放量_萬公噸": "total_emission_10k_ton",
            "人均排放量_公噸/年": "per_capita_emission_ton_per_year",
            "data_time": "data_time",
        }
    )
    # define columns type
    data["year"] = data["year"].astype(int)
    float_cols = set(data.columns) - set(["_id", "_importdate", "year", "data_time"])
    for col in float_cols:
        data[col] = data[col].astype(str)
        data[col] = data[col].str.replace(",", "")
        data[col] = data[col].astype(float)
    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # select columns
    ready_data = data[
        [
            "data_time",
            "year",
            "residential_commercial_sector_emission_10k_ton",
            "residential_commercial_sector_percentage",
            "transportation_sector_emission_10k_ton",
            "transportation_sector_percentage",
            "waste_sector_emission_10k_ton",
            "waste_sector_percentage",
            "industrial_sector_emission_10k_ton",
            "industrial_sector_percentage",
            "agricultural_sector_emission_10k_ton",
            "agricultural_sector_percentage",
            "forest_sector_emission_10k_ton",
            "forest_sector_percentage",
            "total_emission_10k_ton",
            "per_capita_emission_ton_per_year",
        ]
    ]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    lasttime_in_data = data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050601")
dag.create_dag(etl_func=_D050601)
