from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.R0023.crime_etl import crime_etl


def _transfer(**kwargs):
    # Config
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=adf80a2b-b29d-4fca-888c-bcd26ae314e0"
    ENCODING = "cp950"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # ETL
    crime_etl(URL, ENCODING, FROM_CRS, GEOMETRY_TYPE, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="bike_theft")
dag.create_dag(etl_func=_transfer)
