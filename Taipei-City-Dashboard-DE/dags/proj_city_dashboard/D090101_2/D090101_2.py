from airflow import DAG
from operators.common_pipeline import CommonDag


def _D090101_2(**kwargs):
    from proj_city_dashboard.D090101_2.vil_of_school_dist_etl import (
        vil_of_school_dist_etl,
    )

    # Config
    RID = "4ebe14e0-5539-4b43-985c-d3a0a5b351c9"
    SCHOOL_DIST_COL = "國小名稱"

    # ETL
    vil_of_school_dist_etl(RID, SCHOOL_DIST_COL, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D090101_2")
dag.create_dag(etl_func=_D090101_2)
