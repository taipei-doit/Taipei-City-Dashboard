from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.D050303_5.pavement_etl import pavement_etl

def D050303_9(**kwargs):
    '''
    Description: The geometry type of PAC pavement data is MultiLineString. While calculating the 
    area of the pavement, we need to use the original 'area column' as reference.
    '''
    # Config
    file_name = "D050303_9.geojson"
    web_url = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=c50b43ea-d927-492c-a828-06a06389c3ee"
    page_id = "5b277432-f534-4d09-a24c-d3f6b514e042"
    rank_index = 29
    geometry_type = "MultiLineString"
    # ETL
    pavement_etl(file_name, web_url, page_id, rank_index, geometry_type, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050303_9")
dag.create_dag(etl_func=D050303_9)
