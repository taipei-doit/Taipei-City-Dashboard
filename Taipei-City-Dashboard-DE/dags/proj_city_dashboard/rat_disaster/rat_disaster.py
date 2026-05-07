import ssl

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from sqlalchemy import create_engine
from urllib3.util.ssl_ import create_urllib3_context

from airflow import DAG
from operators.common_pipeline import CommonDag
from utils.load_stage import (
    save_dataframe_to_postgresql,
    update_lasttime_in_data_to_dataset_info,
)
from utils.get_time import get_tpe_now_time_str


class _LegacyTLSAdapter(HTTPAdapter):
    # data.taipei 憑證缺 Subject Key Identifier,Python 3.13 預設 VERIFY_X509_STRICT 會拒絕,
    # 仍保留 CA 驗證,只關掉 strict 旗標。
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def _fetch_data_taipei(rid, timeout=60):
    session = requests.Session()
    session.mount("https://", _LegacyTLSAdapter())
    base = f"https://data.taipei/api/v1/dataset/{rid}?scope=resourceAquire"
    first = session.get(base, timeout=timeout).json()
    count = first["result"]["count"]
    results = []
    for offset in range(0, count + 1, 1000):
        url = f"{base}&offset={offset}&limit=1000"
        page = session.get(url, timeout=timeout).json()
        results.extend(page["result"]["results"])
    return results


def _transfer(**kwargs):
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    RID = "86f4c34d-ede3-40d2-8a06-0b154b905bb1"

    raw_list = _fetch_data_taipei(RID)
    raw_data = pd.DataFrame(raw_list)

    data = raw_data.rename(
        columns={
            "行政區": "district",
            "清理廢棄物（噸）": "waste_cleaned_tons",
            "填補鼠洞數": "rat_holes_filled_count",
            "放置捕鼠籠": "mouse_traps_placed_count",
            "施放滅鼠藥劑（克）": "rodenticide_applied_grams",
            "捕獲鼠隻數（包含投藥死亡）": "rats_captured_count",
            "教育宣導場次": "education_outreach_sessions",
            "違規裁處次數": "violation_reports_count",
            "消毒面積（平方公尺）": "disinfection_area_square_meters",
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
