import pandas as pd
from airflow import DAG
from sqlalchemy import create_engine
from operators.common_pipeline import CommonDag
from utils.extract_stage import get_data_taipei_api
from utils.load_stage import (
    save_dataframe_to_postgresql,
    update_lasttime_in_data_to_dataset_info,
)
from utils.get_time import get_tpe_now_time_str


def _transfer(**kwargs):
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    RID = "86f4c34d-ede3-40d2-8a06-0b154b905bb1"

    raw_list = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(raw_list)

    data = raw_data.rename(
        columns={
            "行政區": "district",
            "清理廢棄物(噸)": "waste_cleaned_tons",
            "填補鼠洞數": "rat_holes_filled_count",
            "放置捕鼠籠": "mouse_traps_placed_count",
            "施放滅鼠藥劑(克)": "rodenticide_applied_grams",
            "捕獲鼠隻數(包含投藥死亡)": "rats_captured_count",
            "教育宣導場次": "education_outreach_sessions",
            "違規裁處次數": "violation_reports_count",
            "消毒面積(平方公尺)": "disinfection_area_square_meters",
        }
    )

    numeric_cols = [
        "waste_cleaned_tons",
        "rat_holes_filled_count",
        "mouse_traps_placed_count",
        "rodenticide_applied_grams",
        "rats_captured_count",
        "education_outreach_sessions",
        "violation_reports_count",
        "disinfection_area_square_meters",
    ]
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data["district"] = data["district"].astype(str).str.slice(0, 50)

    ready_data = data[["district"] + numeric_cols]

    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )

    update_lasttime_in_data_to_dataset_info(
        engine,
        airflow_dag_id=dag_id,
        lasttime_in_data=get_tpe_now_time_str(),
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="rat_disaster").create_dag(etl_func=_transfer)
