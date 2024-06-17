from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0019(**kwargs):
    import os

    import geopandas as gpd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        download_file,
        unzip_file_to_target_folder,
    )
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import (
        convert_geometry_to_wkbgeometry,
        convert_polygon_to_multipolygon,
    )
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    geometry_type = "MultiPolygon"
    filename = f"{dag_id}.zip"
    unzip_path = f"{data_path}/{dag_id}"
    ENCODING = "UTF-8"
    FROM_CRS = 3826
    URL = "https://data.moa.gov.tw/OpenData/GetOpenDataFile.aspx?id=I89&FileType=SHP&RID=27238"

    # Extract shpfile
    zip_file = download_file(filename, URL, is_proxy=True)
    unzip_file_to_target_folder(zip_file, unzip_path)
    target_shp_file = [f for f in os.listdir(unzip_path) if f.endswith("shp")][0]
    raw_data = gpd.read_file(
        f"{unzip_path}/{target_shp_file}", encoding=ENCODING, from_crs=FROM_CRS
    )

    # Transform
    gdata = raw_data.copy()
    # rename
    gdata.columns = gdata.columns.str.lower()
    gdata = gdata.rename(
        columns={
            "id": "id",
            "debrisno": "debrisno",  # 土石流潛勢溪流編號
            "county": "county",  # 縣市
            "town": "town",  # 鄉鎮市區
            "vill": "vill",  # 村里
            "overflowno": "overflowno",  # 溢流點編號
            "overflow_x": "overflow_x",
            "overflow_y": "overflow_y",
            "address": "address",  # 保全住戶地址
            "total_res": "total_res",  # 影響範圍內保全住戶總數
            "res_class": "res_class",  # 影響範圍內保全住戶戶數級距
            "risk": "risk",  # 風險等級
            "dbno_old": "dbno_old",  # 土石流潛勢溪流前次編號
        }
    )
    # geometry
    # there some polygon and multipolygon in geometry column, convert them all to multipolygon
    gdata["geometry"] = gdata["geometry"].apply(convert_polygon_to_multipolygon)
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    gdata.drop(columns=["geometry"], inplace=True)
    # secelt columns
    ready_data = gdata[
        [
            "id",
            "debrisno",
            "county",
            "town",
            "vill",
            "overflowno",
            "overflow_x",
            "overflow_y",
            "address",
            "total_res",
            "res_class",
            "risk",
            "dbno_old",
            "wkb_geometry",
        ]
    ]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=geometry_type,
    )
    lasttime_in_data = get_tpe_now_time_str()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0019")
dag.create_dag(etl_func=_R0019)
