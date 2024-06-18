from airflow import DAG
from operators.common_pipeline import CommonDag


def _D090103_2(**kwargs):
    from proj_city_dashboard.D090101_2.vil_of_school_dist_etl import (
        vil_of_school_dist_etl,
    )

    # Config
    RID = "bb9a06d4-69b1-4987-8660-858790f389b3"
    SCHOOL_DIST_COL = "國中學區"

    # ETL
    vil_of_school_dist_etl(RID, SCHOOL_DIST_COL, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D090103_2")
dag.create_dag(etl_func=_D090103_2)
