from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050303_4(**kwargs):
    from proj_city_dashboard.D050302_1.green_land_etl import (
        green_land_etl,
    )

    # Config
    GREEN_LAND_TYPE = "河濱高灘地"
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=e20676c6-0535-4175-b682-9a04be3cd125"
    PAGE_RANK = 11
    GEOMETRY_TYPE = "MultiPolygon"

    # ETL
    green_land_etl(GREEN_LAND_TYPE, URL, PAGE_RANK, GEOMETRY_TYPE, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050303_4")
dag.create_dag(etl_func=_D050303_4)
