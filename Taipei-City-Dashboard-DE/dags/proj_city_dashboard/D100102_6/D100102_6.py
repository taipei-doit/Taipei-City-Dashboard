from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.D100102_1.childcare_etl import childcare_etl


def D100102_6(**kwargs):
    # Config
    RID = "a02ccc34-dd28-4c5d-b527-c5433ec1a453"
    PAGE_ID = "9c9a3f77-8340-48d8-bc0e-f9155521b758"

    # ETL
    childcare_etl(RID, PAGE_ID, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100102_6")
dag.create_dag(etl_func=D100102_6)
