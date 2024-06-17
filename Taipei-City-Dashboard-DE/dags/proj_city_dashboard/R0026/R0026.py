from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.R0023.crime_etl import crime_etl


def _R0026(**kwargs):
    # Config
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=6ecb4c41-fbc9-4b04-b182-a7da6c780f8d"
    ENCODING = "cp950"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # ETL
    crime_etl(URL, ENCODING, FROM_CRS, GEOMETRY_TYPE, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0026")
dag.create_dag(etl_func=_R0026)
