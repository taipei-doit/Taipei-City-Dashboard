from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0022(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID = "aef3466c-6383-4664-b341-6376d1ef9107"

    # Extract
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)

    # Transform
    data = raw_data.copy()
    data = data.rename(columns={"破獲率[％]": "破獲率[%]"})
    year = data["年月別"].str.split("年").str[0]
    month = data["年月別"].str.split("年").str[1]
    year = year.str.zfill(3)
    month = month.str.replace("月", "").str.zfill(2)
    data["年月別"] = year + month + "01"
    data["年月別"] = convert_str_to_time_format(data["年月別"], from_format="%TY%m%d")
    ready_data = data[
        [
            "破獲件數/總計[件]",
            "破獲率[%]",
            "犯罪人口率[人/十萬人]",
            "嫌疑犯[人]",
            "發生件數[件]",
            "破獲件數/他轄[件]",
            "破獲件數/積案[件]",
            "_id",
            "破獲件數/當期[件]",
            "發生率[件/十萬人]",
            "實際員警人數[人]",
            "年月別",
        ]
    ]

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
    lasttime_in_data = ready_data["年月別"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0022")
dag.create_dag(etl_func=_R0022)
