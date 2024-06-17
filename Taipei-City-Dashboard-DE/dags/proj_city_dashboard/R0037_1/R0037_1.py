from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0037_1(**kwargs):
    from proj_city_dashboard.R0037_1.flood_etl import flood_etl

    # Config
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=173adcbe-0f2e-4941-b2bc-127c09db0391"
    PAGE_RANK = 0

    # ETL
    flood_etl(URL, PAGE_RANK, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0037_1")
dag.create_dag(etl_func=_R0037_1)
