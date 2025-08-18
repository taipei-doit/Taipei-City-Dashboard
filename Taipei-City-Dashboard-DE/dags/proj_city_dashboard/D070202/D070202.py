from airflow import DAG
from operators.common_pipeline import CommonDag

def D070202(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format
    from utils.get_time import get_tpe_now_time_str
    
    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")

    # 20250818 來源api 改為csv檔案
    url = 'https://tsis.dbas.gov.taipei/statis/webMain.aspx?sys=220&ymf=5700&kind=21&type=0&funid=A05035701&cycle=4&outmode=12&compmode=0&outkind=1&deflst=2&nzo=1'
    ENCODING = 'utf-8-sig'
    raw_data = pd.read_csv(url, encoding=ENCODING)

    # Extract
    data = raw_data.copy()

    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Transform
    # rename
    data = data.rename(
        columns={
            "統計期": "year",
            "總用戶數[戶]": "total_household",
            "總用電量[千度]": "total_power_usage_mwh",
            "每用戶用電量[度]": "power_usage_kwh_per_household",
            "電燈用戶數[戶]": "total_light_household",
            "電燈用電量[千度]": "total_light_power_usage_mwh",
            "電燈每用戶用電量[度]": "light_power_usage_kwh_per_household",
            "台電自用用電量[千度]": "tpc_self_power_usage_mwh",
            "data_time": "data_time",
        }
    )
    # add column
    data["county"] = "臺北市"
    # standarlize time
    data["year"] = data["year"].str.replace("年", "").astype(int) + 1911
    data["data_time"] = data["year"].astype(str) + "-12-31 23:59:59"
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # Reshape
    ready_data = data[
        [
            "data_time",
            "year",
            "county",
            "total_household",
            "total_power_usage_mwh",
            "power_usage_kwh_per_household",
            "total_light_household",
            "total_light_power_usage_mwh",
            "light_power_usage_kwh_per_household",
            "tpc_self_power_usage_mwh",
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
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D070202")
dag.create_dag(etl_func=D070202)
