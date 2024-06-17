from airflow import DAG
from operators.common_pipeline import CommonDag


def D100106_3(**kwargs):
    """
    Service applicant count per year of maternity hospitals service from data.taipei.

    Explanation:
    -------------
    total_count: There are many columns in original data, we only keep the column
    `生育健康篩檢補助/總計[人次]` as representative.
    """
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        get_data_taipei_api,
        get_data_taipei_file_last_modified_time,
    )
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    raw_data_db_uri = kwargs.get("raw_data_db_uri")
    data_folder = kwargs.get("data_folder")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    # proxies = kwargs.get('proxies')
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    VILLAGE_TABLE = "tw_village"
    # Manually set
    RID = "c8f5b53d-ef3d-4321-ae8e-58cd2a5ee73c"
    PAGE_ID = "a6394e3f-3514-4542-87bd-de4310a40db3"
    from_crs = 4326

    # Extract
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)

    # Transform
    # Rename
    data = raw_data
    # Filter columns
    keep_col = [
        "年份",
        "月份",
        "區域代碼",
        "區域別",
        "性別",
        "總計",
        "0歲數量",
        "1歲數量",
        "2歲數量",
        "3歲數量",
        "4歲數量",
        "5歲數量",
    ]
    data = data[keep_col]
    # Transfer year from ROC to AD
    data = data.copy()
    data["年份"] = data["年份"].astype(int) + 1911
    data["年份"] = data["年份"].astype(str)
    data["月份"] = data["月份"].astype(str)
    data["timestamp"] = data["年份"] + "-" + data["月份"]
    data["timestamp"] = pd.to_datetime(data["timestamp"], format="%Y-%m")
    col_dict = {
        "年份": "year",
        "月份": "month",
        "區域代碼": "district_code",
        "區域別": "district",
        "性別": "gender",
        "總計": "total",
        "0歲數量": "age_0",
        "1歲數量": "age_1",
        "2歲數量": "age_2",
        "3歲數量": "age_3",
        "4歲數量": "age_4",
        "5歲數量": "age_5",
    }
    data.rename(columns=col_dict, inplace=True)
    # Set condition
    condition = (data["district"].str.contains("總計")) & (data["gender"] == "計")
    data = data[condition]
    # Filter numeric columns
    data = data.copy()
    num_col = ["total", "age_0", "age_1", "age_2", "age_3", "age_4", "age_5"]
    data[num_col] = data[num_col].apply(pd.to_numeric)
    # Count group age
    data.loc[:, "age_0_1"] = data["age_0"] + data["age_1"]
    data.loc[:, "age_2_3"] = data["age_2"] + data["age_3"]
    data.loc[:, "age_4_5"] = data["age_4"] + data["age_5"]
    keep_col = [
        "district_code",
        "district",
        "gender",
        "total",
        "timestamp",
        "age_0_1",
        "age_2_3",
        "age_4_5",
    ]
    data = data[keep_col]
    data = data.reset_index(drop=True)
    # Time
    data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    ready_data = data.copy()

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100106_3")
dag.create_dag(etl_func=D100106_3)
