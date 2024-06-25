from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.D100102_1.childcare_etl import childcare_etl


def D100102_8(**kwargs):
    # Config
    RID = "1015e1db-bbf0-4cef-9bea-9928e84b3735"
    PAGE_ID = "01ac5a1d-dfc3-44c7-84a7-6d76bcb2879b"

    # ETL
    childcare_etl(RID, PAGE_ID, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100102_8")
dag.create_dag(etl_func=D100102_8)
