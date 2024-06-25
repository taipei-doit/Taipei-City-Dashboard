from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.D100102_1.childcare_etl import childcare_etl


def D100102_5(**kwargs):
    # Config
    RID = "f1418a7a-4bdf-41fc-869c-63703dc16363"
    PAGE_ID = "7c66efcd-d073-401c-b18a-7a46728776c4"

    # ETL
    childcare_etl(RID, PAGE_ID, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100102_5")
dag.create_dag(etl_func=D100102_5)
