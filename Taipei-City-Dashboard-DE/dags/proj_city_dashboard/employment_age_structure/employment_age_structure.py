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
    from utils.get_time import get_tpe_now_time_str
    proxies = kwargs.get("proxies")

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    url = 'https://data.taipei/api/v1/dataset/71185df2-d7a2-48f2-9bb5-192b59737610?scope=resourceAquire'
    res = requests.get(url, proxies=proxies, timeout=60)
    if res.status_code != 200:
        raise ValueError(f"Request failed! status: {res.status_code}")
    res_json = res.json()
    
    # Debug: Check the structure of the response
    print(f"Response type: {type(res_json)}")
    if isinstance(res_json, dict):
        print(f"Available keys: {list(res_json.keys())}")
    elif isinstance(res_json, list):
        print(f"Response is a list with {len(res_json)} items")
        if len(res_json) > 0:
            print(f"First item type: {type(res_json[0])}")
            if isinstance(res_json[0], dict):
                print(f"First item keys: {list(res_json[0].keys())}")
    
    # Handle different response structures
    if isinstance(res_json, list):
        data = pd.DataFrame(res_json)
    elif isinstance(res_json, dict) and "data" in res_json:
        data = pd.DataFrame(res_json["data"])
    elif isinstance(res_json, dict) and "result" in res_json:
        # Check if result contains results array
        if isinstance(res_json["result"], dict) and "results" in res_json["result"]:
            data = pd.DataFrame(res_json["result"]["results"])
            print(f"Found data in result.results with {len(res_json['result']['results'])} items")
        elif isinstance(res_json["result"], list):
            data = pd.DataFrame(res_json["result"])
            print(f"Found data in result with {len(res_json['result'])} items")
        else:
            raise ValueError(f"Unexpected result structure: {type(res_json['result'])}")
    else:
        # Try to find the data in the response
        if isinstance(res_json, dict):
            # Look for common data keys
            data_keys = ["data", "result", "results", "records", "items"]
            data_found = False
            for key in data_keys:
                if key in res_json and isinstance(res_json[key], list):
                    data = pd.DataFrame(res_json[key])
                    print(f"Found data in key: {key}")
                    data_found = True
                    break
            if not data_found:
                raise ValueError(f"Could not find data in response. Available keys: {list(res_json.keys())}")
        else:
            raise ValueError(f"Unexpected response structure: {type(res_json)}")

    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    
    # Debug: Print available columns
    print("Available columns:", list(data.columns))
    
    data = data.rename(
        columns={
                    "年平均別": "year",
                    "性別": "gender",
                    "年齡結構": "age_structure",
                    # "實數[千人]": "actual_number_thousand",
                    "百分比[％]": "percentage",
        }
    )
    
    # Check if percentage column exists after rename and handle conversion safely
    if 'percentage' in data.columns:
        # Replace '-' with None and handle conversion to float safely
        data['percentage'] = data['percentage'].replace('-', None)
        data['percentage'] = pd.to_numeric(data['percentage'], errors='coerce')
    else:
        print("Warning: 'percentage' column not found after rename operation")
        print("Available columns after rename:", list(data.columns))
 
    data['year'] = data['year'].replace('年', '', regex=True)
    data['year'] = data['year'].astype(int) + 1911
    
    # Select only existing columns
    available_columns = ["year", "gender", "age_structure", "data_time"]
    if 'percentage' in data.columns:
        available_columns.insert(-1, "percentage")  # Insert before data_time
    
    data = data[available_columns]
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=data,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, data["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="employment_age_structure")
dag.create_dag(etl_func=_transfer)
