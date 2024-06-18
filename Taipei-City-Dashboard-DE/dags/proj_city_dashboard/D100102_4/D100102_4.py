from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.D100102_1.childcare_etl import childcare_etl


def D100102_4(**kwargs):
    # Config
    RID = "57685fb2-cc92-4874-8588-e5a1b1b15b50"
    PAGE_ID = "a7462972-0380-4987-99fb-2071e798ce66"

    # ETL
    childcare_etl(RID, PAGE_ID, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100102_4")
dag.create_dag(etl_func=D100102_4)
