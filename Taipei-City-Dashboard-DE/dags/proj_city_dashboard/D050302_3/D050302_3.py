from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050302_3(**kwargs):
    from proj_city_dashboard.D050302_1.green_land_etl import (
        green_land_etl,
    )

    # Config
    GREEN_LAND_TYPE = "都市計畫保護區、農業區"
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=9e895ea7-8a73-48b0-8882-2ca3cd48115f"
    PAGE_RANK = 29
    GEOMETRY_TYPE = "MultiPolygon"

    # ETL
    green_land_etl(GREEN_LAND_TYPE, URL, PAGE_RANK, GEOMETRY_TYPE, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050302_3")
dag.create_dag(etl_func=_D050302_3)
