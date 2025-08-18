from airflow import DAG
from operators.common_pipeline import CommonDag
from io import StringIO
import requests


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    # 20250818 來源api 改為csv檔案
    url = 'https://tsis.dbas.gov.taipei/statis/webMain.aspx?sys=220&ymf=5700&kind=21&type=0&funid=a05002601&cycle=4&outmode=12&compmode=0&outkind=1&deflst=2&nzo=1'
    response = requests.get(url)
    response.encoding = 'utf-8'
    raw_data = pd.read_csv(StringIO(response.text))

    data = raw_data.copy()
    
    data = data.rename(
        columns={
            "年底別": "end_of_year",
            "幼年人口數[人]": "young_population",
            "幼年人口占全市人口比率[％]": "young_population_percentage",
            "青壯年人口數[人]": "working_age_population",
            "青壯年人口占全市人口比率[％]": "working_age_population_percentage",
            "老年人口數[人]": "elderly_population",
            "老年人口占全市人口比率[％]": "elderly_population_percentage",
            "扶老比[％]": "elderly_dependency_ratio",
            "扶幼比[％]": "youth_dependency_ratio",
            "扶養比[％]": "total_dependency_ratio",
            "老化指數[％]": "aging_index",
        }
    )
    data['end_of_year'] = data['end_of_year'].replace('年', '', regex=True)
    data['end_of_year'] = data['end_of_year'].astype(int) + 1911
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
