from airflow import DAG
from operators.common_pipeline import CommonDag


def D030101_1(**kwargs):
    import geopandas as gpd
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    from utils.transform_time import convert_str_to_time_format
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = r"https://tpnco.blob.core.windows.net/blobfs/Data/TP_SIDEWORK.json"
    GEOMETRY_TYPE = "MultiPolygon"
    filename = f"{dag_id}.json"
    ENCODING = "UTF-8"
    FROM_CRS = 3826

    # Extract
    local_file = download_file(filename, URL, is_proxy=True, timeout=300)
    raw = gpd.read_file(local_file, encoding=ENCODING)
    gdata = raw.copy()

    # Transform
    # define column type
    gdata.columns = gdata.columns.str.lower()
    gdata["objectid"] = gdata["objectid"].astype(str)
    gdata["data_time"] = get_tpe_now_time_str()
    gdata["data_time"] = convert_str_to_time_format(gdata["data_time"])
    # geometry
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    # reshape
    col_map = {
        "objectid": "id",
        "town_n": "dist",
        "name_road": "name",  # 人行道名稱
        "pstart": "start_road",  # 起始路名
        "pend": "end_road",  # 結束路名
        "sw_direct": "direction",  # 街道的哪一側
        "sw_leng_itemvalue": "length",
        "sw_wth_itemvalue": "width",
        "shape_ar_itemvalue": "area",
        "sww_wth": "clear_width",  # 淨寬
        "geometry": "geometry",
    }
    gdata = gdata.rename(columns=col_map)
    # select column
    ready_data = gdata[
        [
            "data_time",
            "id",
            "dist",
            "name",
            "start_road",
            "end_road",
            "length",
            "width",
            "area",
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
        geometry_type=GEOMETRY_TYPE,
    )
    lasttime_in_data = gdata["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D030101_1")
dag.create_dag(etl_func=D030101_1)
