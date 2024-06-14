from airflow import DAG
from operators.common_pipeline import CommonDag


def _D080102(**kwargs):
    from proj_city_dashboard.D080101.cdc_visit_case_etl import cdc_visit_case_etl
    
    URL = "https://od.cdc.gov.tw/eic/NHI_EnteroviralInfection.csv"
    DIEASE_NAME = '腸病毒'
    
    cdc_visit_case_etl(URL, DIEASE_NAME, **kwargs)



dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D080102")
dag.create_dag(etl_func=_D080102)
