from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050302_1(**kwargs):
    from proj_city_dashboard.D050302_1.green_land_etl import (
        green_land_etl,
    )

    # Config
    GREEN_LAND_TYPE = "野雁保護區"
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=9f9205e5-fa3e-42b1-b059-02def57f8f37"
    PAGE_RANK = 30
    GEOMETRY_TYPE = "MultiPolygon"

    # ETL
    green_land_etl(GREEN_LAND_TYPE, URL, PAGE_RANK, GEOMETRY_TYPE, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050302_1")
dag.create_dag(etl_func=_D050302_1)
