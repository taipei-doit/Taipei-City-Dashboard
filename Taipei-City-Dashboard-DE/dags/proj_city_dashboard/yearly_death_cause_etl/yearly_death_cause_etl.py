from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    import requests
    from io import StringIO
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://tsis.dbas.gov.taipei/statis/webMain.aspx?sys=220&ymf=8100&kind=21&type=0&funid=A05032401&cycle=4&outmode=12&compmode=0&outkind=3&deflst=2&nzo=1"

    raw_data = pd.read_csv(URL , encoding='utf-8-sig')
    # Transform
    data = raw_data.copy()
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # rename
    # 重命名欄位
    data = data.rename(columns={
        '統計期': 'year',
        '死因別': 'death_cause',
        '死亡人數/合計[人]': 'death_count',
        '死亡率/合計[人/十萬人口]': 'mortality_rate'
    })
    # 轉西元年
    data["year"] = data["year"].str.replace("年", "", regex=False).astype(int) + 1911
    # Load
    data = data[["year", "death_cause", "death_count", "mortality_rate", "data_time"]]
    
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, data["data_time"].max()
        )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="yearly_death_cause_etl")
dag.create_dag(etl_func=_transfer)
