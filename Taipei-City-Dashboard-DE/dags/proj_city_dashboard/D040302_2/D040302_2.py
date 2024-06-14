from airflow import DAG
from operators.common_pipeline import CommonDag


def D040302_2(**kwargs):
    from proj_city_dashboard.D040302_1.today_road_use_etl import today_road_use_etl

    URL = "https://tpnco.blob.core.windows.net/blobfs/Rally/TodayRallyCase.json"

    today_road_use_etl(URL, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D040302_2")
dag.create_dag(etl_func=D040302_2)
