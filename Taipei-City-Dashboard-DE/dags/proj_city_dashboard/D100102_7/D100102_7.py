from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.D100102_1.childcare_etl import childcare_etl


def D100102_7(**kwargs):
    # Config
    RID = "e7cdaca3-e9da-46f9-b857-395e6e8e06a6"
    PAGE_ID = "081df75e-85c7-464c-b125-546920911c5c"

    # ETL - 使用 CSV 來源
    childcare_etl(RID, PAGE_ID, source_type="csv", **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100102_7")
dag.create_dag(etl_func=D100102_7)
