from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.D100102_1.childcare_etl import childcare_etl


def D100102_2(**kwargs):
    # Config
    RID = "4bfa01ad-7ba0-4b7a-9c1b-f9c58a2cd751"
    PAGE_ID = "7262cdae-18e7-4d33-a842-4978cbc84d43"

    # ETL
    childcare_etl(RID, PAGE_ID, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100102_2")
dag.create_dag(etl_func=D100102_2)
