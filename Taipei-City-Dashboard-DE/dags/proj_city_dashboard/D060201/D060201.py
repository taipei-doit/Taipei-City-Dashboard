from airflow import DAG
from operators.common_pipeline import CommonDag


def _D060201(**kwargs):
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    def get_datataipei_file_rid(page_id):
        url = f"https://data.taipei/api/frontstage/tpeod/dataset.view?id={page_id}"
        res = requests.get(url)
        res.raise_for_status()
        res_json = res.json()
        data_list = res_json["payload"]["resources"]
        url_list = {}
        for data in data_list:
            file_tag = data["name"].split("月")[0] + "月"
            rid = data["rid"]
            url_list[file_tag] = rid
        return url_list

    def get_existing_data(ready_data_db_uri, table_name, column="file_tag"):
        engine = create_engine(ready_data_db_uri)
        sql = f"select distinct {column} from {table_name}"
        existing_tag = pd.read_sql(sql, engine).iloc[:, 0]
        return existing_tag.tolist()

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    PAGE_ID = "a4484aa2-533c-45a1-88fd-de0c6276bcfe"

    # Extract
    # get all data url
    data_list = get_datataipei_file_rid(PAGE_ID)
    # filter out existing year
    existing_month = get_existing_data(ready_data_db_uri, default_table)
    new_data_list = {k: v for k, v in data_list.items() if k not in existing_month}
    # get data
    raw_datas = []
    for file_tag, rid in new_data_list.items():
        raw_data = get_data_taipei_api(rid, output_format="dataframe")
        raw_data["file_tag"] = file_tag
        raw_datas.append(raw_data)

    # Transform
    ready_datas = []
    for raw_data in raw_datas:
        data = raw_data.copy()
        # rename
        data = data.rename(
            columns={
                "file_tag": "file_tag",
                "區域別": "town",
                "救護出勤合計次數": "total_case",
                "送醫次數": "to_hospital_case",
                "未接觸次數": "no_contact_case",
                "有接觸未運送次數": "contact_not_transport_case",
                "出勤待命次數": "on_duty_case",
                "data_time": "data_time",
            }
        )
        # fill missing columns, cause old data may not have all columns
        select_columns = [
            "file_tag",
            "town",
            "total_case",
            "to_hospital_case",
            "no_contact_case",
            "contact_not_transport_case",
            "on_duty_case",
            "data_time",
        ]
        for col in select_columns:
            if col not in list(data.columns):
                data[col] = None
        # define data type
        num_cols = [
            "total_case",
            "to_hospital_case",
            "no_contact_case",
            "contact_not_transport_case",
            "on_duty_case",
        ]
        for col in num_cols:
            data[col] = pd.to_numeric(data[col], errors="coerce")
        # standardize time
        data["data_time"] = convert_str_to_time_format(data["data_time"])
        # select columns
        ready_data = data[select_columns]
        ready_datas.append(ready_data)

    # Load
    engine = create_engine(ready_data_db_uri)
    for ready_data in ready_datas:
        save_dataframe_to_postgresql(
            engine,
            data=ready_data,
            load_behavior=load_behavior,
            default_table=default_table,
        )
        update_lasttime_in_data_to_dataset_info(
            engine, dag_id, data["data_time"].max()
        )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D060201")
dag.create_dag(etl_func=_D060201)
