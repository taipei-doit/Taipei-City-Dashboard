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
    update_lasttime_in_data_to_dataset_info,
)
from utils.auth_cht import CHTAuth
from airflow.models import Variable
import json
import logging

def _cht_e2(**kwargs):
    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    now_time = datetime.now(timezone(timedelta(seconds=28800)))  # Taiwan timezone
    cht = CHTAuth()
    access_token = cht.get_token(now_time)
    url = Variable.get("E2_API_URL")
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'curl/7.68.0'
        }   
    data_frames = []
    stay_mins = [10,30,60]
    today = datetime.strftime(datetime.now(timezone(timedelta(seconds=28800))), "%Y%m%d")
    for mins in stay_mins:
        payload = json.dumps({
            "token": access_token,
            "yyyymmdd": today,
            "stay_mins": mins,
            "api_id": "30"
        })
        resp = requests.post(url, headers=headers, data=payload, proxies=PROXIES, verify=False)
        if resp.status_code != 200:
            raise ValueError(f"Request failed! status: {resp.status_code}")
    
        res = resp.json()
        if res['status'] == 1:
            data = res.get("data", [])
            if data:
                df = pd.DataFrame(data)
                df["status"] = res['status']
                df["api_id"] = res['api_id']
                df['data_time'] = get_tpe_now_time_str()
                df['msg'] = res['msg']
                df["stay_mins"] = mins  # 添加停留時間作為欄位
                data_frames.append(df)
            combined_df = pd.concat(data_frames, ignore_index=True)
            logging.info(combined_df.head)

        else:
            return res

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=combined_df,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, combined_df["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="cht_e2")
dag.create_dag(etl_func=_cht_e2)
