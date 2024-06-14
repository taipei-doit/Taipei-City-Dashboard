from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050303_1(**kwargs):
    from proj_city_dashboard.D050302_1.green_land_etl import (
        green_land_etl,
    )

    # Config
    GREEN_LAND_TYPE = "公園"
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=f3ce4bb6-712a-41ae-902b-f8a6099eac85"
    PAGE_RANK = 14
    GEOMETRY_TYPE = "MultiPolygon"

    # ETL
    green_land_etl(GREEN_LAND_TYPE, URL, PAGE_RANK, GEOMETRY_TYPE, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050303_1")
dag.create_dag(etl_func=_D050303_1)
