from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.D100102_1.childcare_etl import childcare_etl


def D100102_1(**kwargs):
    # Config
    RID = "5c09f39f-79cc-45b8-be8e-9b3ea8b220e3"
    PAGE_ID = "fd4779d0-827d-4ab3-8f65-2a356abad6d9"

    # ETL
    childcare_etl(RID, PAGE_ID, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100102_1")
dag.create_dag(etl_func=D100102_1)
