from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0037_2(**kwargs):
    from proj_city_dashboard.R0037_1.flood_etl import flood_etl

    # Config
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=4b14c3a0-fcf2-48d4-9c93-e27784cae29d"
    PAGE_RANK = 0

    # ETL
    flood_etl(URL, PAGE_RANK, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0037_2")
dag.create_dag(etl_func=_R0037_2)
