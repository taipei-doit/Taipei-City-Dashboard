from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.R0023.crime_etl import crime_etl


def _R0024(**kwargs):
    # Config
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=967faed7-ea9b-4698-970a-d335d5e4ccc3"
    ENCODING = "cp950"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # ETL
    crime_etl(URL, ENCODING, FROM_CRS, GEOMETRY_TYPE, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0024")
dag.create_dag(etl_func=_R0024)
