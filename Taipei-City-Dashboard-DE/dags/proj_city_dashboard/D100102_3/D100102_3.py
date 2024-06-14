from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.D100102_1.childcare_etl import childcare_etl


def D100102_3(**kwargs):
    # Config
    RID = "5cf938d7-350e-433b-b8be-280710038d74"
    PAGE_ID = "41c729ce-c848-492a-b7a6-db468f06c17c"

    # ETL
    childcare_etl(RID, PAGE_ID, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100102_3")
dag.create_dag(etl_func=D100102_3)
