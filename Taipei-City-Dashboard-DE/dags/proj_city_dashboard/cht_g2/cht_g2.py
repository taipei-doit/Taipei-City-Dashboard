from airflow import DAG
from operators.common_pipeline import CommonDag
from datetime import datetime,timedelta,timezone
import pandas as pd
import requests
from settings.global_config import PROXIES
from sqlalchemy import create_engine
from utils.get_time import get_tpe_now_time_str
from utils.load_stage import (
    save_dataframe_to_postgresql,
    update_lasttime_in_data_to_dataset_info)
from utils.auth_cht import CHTAuth
from airflow.models import Variable
import json
import logging

def _cht_g2(**kwargs):
    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    now_time = datetime.now(timezone(timedelta(seconds=28800)))  # Taiwan timezone
    cht = CHTAuth()
    access_token = cht.get_token(now_time)
 

    url = Variable.get("G2_G4_API_URL")
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'curl/7.68.0'
        }   

    playload = json.dumps({
        "token": access_token,
        "split": "10",
        "api_id": "31"
    })
    resp = requests.post(url, headers=headers, data=playload, proxies=PROXIES,verify=False)
    if resp.status_code != 200:
        raise ValueError(f"Request failed! status: {resp.status_code}")

    res = resp.json()
    if res['status'] == 1:
        raw_data = pd.DataFrame(res["data"])

        # Define county mapping
        county_mapping = {
            "台北市": "A", "台中市": "B", "基隆市": "C", "台南市": "D", "高雄市": "E",
            "新北市": "F", "宜蘭縣": "G", "桃園市": "H", "嘉義市": "I", "新竹縣": "J",
            "苗栗縣": "K", "南投縣": "M", "彰化縣": "N", "新竹市": "O", "雲林縣": "P",
            "嘉義縣": "Q", "屏東縣": "T", "花蓮縣": "U", "台東縣": "V", "澎湖縣": "X",
            "金門縣": "W", "連江縣": "Z"
        }

        # Split and map counties
        def split_counties(county_str):
            county_data = dict(item.split(":") for item in county_str.split(";") if item)
            mapped_data = {county_mapping[key]: int(value) for key, value in county_data.items() if key in county_mapping}
            return mapped_data

        df_county_split = raw_data['county'].apply(split_counties)

        # # Expand to separate columns
        df_expanded = df_county_split.apply(pd.Series).fillna(0).astype(int)
        df = pd.concat([raw_data, df_expanded], axis=1).drop(columns=['county'])
        df['data_time'] = get_tpe_now_time_str()
        df['status'] = res['status']
        df['api_id'] =res['api_id']
        df['msg'] = res['msg']
        logging.info(df.head)

    else:
        return res

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=df,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, df["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="cht_g2")
dag.create_dag(etl_func=_cht_g2)
