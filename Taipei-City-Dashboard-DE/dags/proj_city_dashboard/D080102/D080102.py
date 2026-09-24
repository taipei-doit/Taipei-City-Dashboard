import logging

from airflow import DAG
from requests.exceptions import ConnectTimeout

from operators.common_pipeline import CommonDag


def _D080102(**kwargs):
    from proj_city_dashboard.D080101.cdc_visit_case_etl import cdc_visit_case_etl
    
    URL = "https://od.cdc.gov.tw/eic/NHI_EnteroviralInfection.csv"
    HTTP_FALLBACK_URL = "http://od.cdc.gov.tw/eic/NHI_EnteroviralInfection.csv"
    DIEASE_NAME = '腸病毒'
    
    try:
        cdc_visit_case_etl(URL, DIEASE_NAME, **kwargs)
    except ConnectTimeout:
        logging.warning("CDC HTTPS connection timed out; using the HTTP CSV fallback")
        cdc_visit_case_etl(HTTP_FALLBACK_URL, DIEASE_NAME, **kwargs)



dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D080102")
dag.create_dag(etl_func=_D080102)
