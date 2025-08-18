from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    # 20250818 來源api 改為csv檔案
    URL = 'https://tsis.dbas.gov.taipei/statis/webMain.aspx?sys=220&ymf=5700&kind=21&type=0&funid=a05002601&cycle=4&outmode=12&compmode=0&outkind=1&deflst=2&nzo=1'
    ENCODING = 'utf-8-sig'
    raw_data = pd.read_csv(URL, encoding=ENCODING)

    data = raw_data.copy()
    
    # Debug: Print available columns to understand the actual column names
    print("Available columns:", list(data.columns))
    
    # Create a more flexible column mapping that handles both full-width and half-width characters
    column_mapping = {}
    for col in data.columns:
        if "統計期" in col:
            column_mapping[col] = "end_of_year"
        elif "幼年人口數" in col:
            column_mapping[col] = "young_population"
        elif "幼年人口占全市人口比率" in col:
            column_mapping[col] = "young_population_percentage"
        elif "青壯年人口數" in col:
            column_mapping[col] = "working_age_population"
        elif "青壯年人口占全市人口比率" in col:
            column_mapping[col] = "working_age_population_percentage"
        elif "老年人口數" in col:
            column_mapping[col] = "elderly_population"
        elif "老年人口占全市人口比率" in col:
            column_mapping[col] = "elderly_population_percentage"
        elif "扶老比" in col:
            column_mapping[col] = "elderly_dependency_ratio"
        elif "扶幼比" in col:
            column_mapping[col] = "youth_dependency_ratio"
        elif "扶養比" in col:
            column_mapping[col] = "total_dependency_ratio"
        elif "老化指數" in col:
            column_mapping[col] = "aging_index"
    
    print("Column mapping:", column_mapping)
    data = data.rename(columns=column_mapping)
    
    # Clean up end_of_year column by removing non-numeric characters
    data['end_of_year'] = data['end_of_year'].str.replace(r'[^\d]', '', regex=True)
    data['end_of_year'] = data['end_of_year'].astype(int) + 1911
    
    # Add data_time column
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
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

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="dependency_ratio_and_aging_index")
dag.create_dag(etl_func=_transfer)
