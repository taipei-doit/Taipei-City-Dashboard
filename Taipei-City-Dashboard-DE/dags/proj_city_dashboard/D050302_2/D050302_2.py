from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050302_2(**kwargs):
    from proj_city_dashboard.D050302_1.green_land_etl import (
        green_land_etl,
    )

    # Config
    GREEN_LAND_TYPE = "自然保留區"
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=9849f543-f707-4d76-8156-190b3f5af95b"
    PAGE_RANK = 36
    GEOMETRY_TYPE = "MultiPolygon"

    # ETL
    green_land_etl(GREEN_LAND_TYPE, URL, PAGE_RANK, GEOMETRY_TYPE, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050302_2")
dag.create_dag(etl_func=_D050302_2)
