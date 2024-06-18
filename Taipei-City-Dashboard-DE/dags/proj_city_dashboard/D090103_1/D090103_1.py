from airflow import DAG
from operators.common_pipeline import CommonDag


def D090103_1(**kwargs):
    from proj_city_dashboard.D090101_1.school_dist_etl import school_dist_etl

    # Config
    RID = "a97b9fae-c20f-4a33-a5d3-fa36e64c304f"
    COL_MAP = {
        "學校名稱": "name",
        "校址": "addr",
        "區別": "dist",
        "區分": "dist_of_school_dist",
        "學區範圍/里別": "school_district",
        "電話及傳真": "phone",
    }

    # ETL
    school_dist_etl(RID, COL_MAP, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D090103_1")
dag.create_dag(etl_func=D090103_1)
