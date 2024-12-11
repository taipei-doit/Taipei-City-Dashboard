from airflow import DAG
from operators.common_pipeline import CommonDag
from datetime import datetime,timedelta,timezone

def _che_e2(**kwargs):
    import geopandas as gpd
    import numpy as np
    import pandas as pd
    import requests
    import time
    from geopandas.tools import sjoin
    from settings.global_config import PROXIES
    from shapely import wkt
    from sqlalchemy import create_engine
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format
    from utils.auth_che import CHEAuth
	from airflow.models import Variable

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    now_time = datetime.now(timezone(timedelta(seconds=28800)))  # Taiwan timezone
    access_token = CHEAuth.get_token(now_time)
    url = Variable.get("G2_API_URL")
    headers = {
        'Content-Type': 'application/json'
        }   
    data_frames = []
    stay_mins = [10,30,60]
    for mins in stay_mins:
        payload = {
            "token": access_token,
            "yyyymmdd": now_time,
            "stay_mins": mins,
            "api_id": "30"
        }
        resp = requests.post(url, headers=headers, data=payload, proxies=PROXIES)
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
            # df = dict()
            # df['status_msg'] = res['msg']
            # df['event'] = res['data'][0]['ev_name']
            # df['allcnt'] = res['data'][0]['allcnt']
            # df['male'] = res['data'][0]['male']
            # df['female'] = res['data'][0]['female']
            # df['age19'] = res['data'][0]['age19']
            # df['age29'] = res['data'][0]['age29']
            # df['age39'] = res['data'][0]['age39']
            # df['age49'] = res['data'][0]['age49']
            # df['age59'] = res['data'][0]['age59']
            # df['age60'] = res['data'][0]['age60']
            # df['A'] = res['data'][0]['A']
            # df['B'] = res['data'][0]['B']
            # df['C'] = res['data'][0]['C']
            # df['D'] = res['data'][0]['D']
            # df['E'] = res['data'][0]['E']
            # df['F'] = res['data'][0]['F']
            # df['G'] = res['data'][0]['G']
            # df['taoyuan_city'] = res['data'][0]['H']
            # df['chiayi_city'] = res['data'][0]['I']
            # df['hsinchu_county'] = res['data'][0]['J']
            # df['miaoli_county'] = res['data'][0]['K']
            # df['nantou_county'] = res['data'][0]['M']
            # df['changhua_county'] = res['data'][0]['N']
            # df['hsinchu_city'] = res['data'][0]['O']
            # df['yunlin_county'] = res['data'][0]['P']
            # df['chiayi_county'] = res['data'][0]['Q']
            # df['pingtung_county'] = res['data'][0]['T']
            # df['hualien_county'] = res['data'][0]['U']
            # df['taitung_county'] = res['data'][0]['V']
            # df['penghu_county'] = res['data'][0]['X']
            # df['kinmen_county'] = res['data'][0]['W']
            # df['lienchiang_county'] = res['data'][0]['Z']
            # df['data_time'] = get_tpe_now_time_str()
            # df['stay_mins'] = mins
        else:
            print(res)
            break

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

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="che_e2")
dag.create_dag(etl_func=_che_e2)
