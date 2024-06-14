from airflow import DAG
from operators.common_pipeline import CommonDag


def D090101_1(**kwargs):
    from proj_city_dashboard.D090101_1.school_dist_etl import school_dist_etl

    # Config
    RID = "aacc6194-39d5-4888-be8e-3dc62f464a4c"
    COL_MAP = {
        "學校名稱": "name",
        "校址": "addr",
        "區別": "dist",
        "區分": "dist_of_school_dist",
        "里別": "school_district",
        "電話號碼": "phone",
    }

    # ETL
    school_dist_etl(RID, COL_MAP, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D090101_1")
dag.create_dag(etl_func=D090101_1)
