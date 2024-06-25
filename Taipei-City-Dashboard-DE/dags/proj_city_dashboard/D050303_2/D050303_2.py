from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050303_2(**kwargs):
    from proj_city_dashboard.D050302_1.green_land_etl import (
        green_land_etl,
    )

    # Config
    GREEN_LAND_TYPE = "校園綠化"
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=fe4cdaf5-2882-489b-bb2f-a3b6947b3ca1"
    PAGE_RANK = 3
    GEOMETRY_TYPE = "MultiPolygon"

    # ETL
    green_land_etl(GREEN_LAND_TYPE, URL, PAGE_RANK, GEOMETRY_TYPE, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050303_2")
dag.create_dag(etl_func=_D050303_2)
