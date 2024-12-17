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


def _cht_g4(**kwargs):
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
        "split": "1",
        "api_id": "33"
    })
    resp = requests.post(url, headers=headers, data=playload, proxies=PROXIES,verify=False)
    if resp.status_code != 200:
        raise ValueError(f"Request failed! status: {resp.status_code}")

    res = resp.json()
    if res['status'] == 1:
        raw_data = []
        for entry in res["data"]:
            ev_name = entry["name"]
            grids = entry["grids"]
            for grid in grids:
                raw_data.append({
                    "ev_name": ev_name,
                    "gid": grid["gid"],
                    "population": grid["population"]
                })
        # Convert the structured data to a DataFrame
        raw_data_df = pd.DataFrame(raw_data)
        # sql = """select ev_name, gid from public.nye_grid"""
        # g4_grids = pd.read_sql(sql, engine)
        # raw_data_df['gid'] = raw_data_df['gid'].astype(str)
        # g4_grids['gid'] = g4_grids['gid'].astype(str)
        # merged_df = raw_data_df.merge(g4_grids, on='gid', how='left', suffixes=('_a', '_b'))
        # # 更新 ev_name，當 gid 相同時使用 df_b 的 ev_name
        # merged_df['ev_name'] = merged_df['ev_name_b'].combine_first(merged_df['ev_name_a'])
        # merged_df = merged_df.drop(columns=['ev_name_b','ev_name_a'])
        # merged_df['gid'] = merged_df['gid'].astype(int)
        # Add additional columns
        raw_data_df['time'] = res['time']
        raw_data_df['data_time'] = get_tpe_now_time_str()
        raw_data_df['status'] = res['status']
        raw_data_df['api_id'] = res['api_id']
        raw_data_df['msg'] = res['msg']
        logging.info(raw_data_df.columns)
    else:
        return res
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=raw_data_df,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, raw_data_df["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="cht_g4")
dag.create_dag(etl_func=_cht_g4)
