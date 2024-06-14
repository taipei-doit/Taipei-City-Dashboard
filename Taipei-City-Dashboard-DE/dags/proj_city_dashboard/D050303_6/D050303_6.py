from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.D050303_5.pavement_etl import pavement_etl

def D050303_6(**kwargs):
    # Config
    file_name = "D050303_6.geojson"
    web_url = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=89fe1553-6c19-4e10-be23-fc8027d27c71"
    page_id = "5b277432-f534-4d09-a24c-d3f6b514e042"
    rank_index = 26
    geometry_type = "MultiPolygon"
    # ETL
    pavement_etl(file_name, web_url, page_id, rank_index, geometry_type, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050303_6")
dag.create_dag(etl_func=D050303_6)
