from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0076(**kwargs):
    import json

    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://tpnco.blob.core.windows.net/blobfs/Nethers.json"
    GEOMETRY_TYPE = "Point"
    file_name = f"{dag_id}.json"
    FROM_CRS = 4326


    # Extract
    # download file
    local_file = download_file(file_name, URL, is_proxy=True)
    with open(local_file) as json_file:
        res = json.load(json_file)
    # parse
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Transform
    data = raw_data.copy()
    # rename
    data.columns = data.columns.str.lower()
    data = data.rename(
        columns={
            "netherkind": "nether_kind",  # 地下道類型(A-人行, B-車行)
            "adminunit": "admin_unit",  # 轄下機關
            "countycode": "city_code",  # 所在縣市代碼
            "areacode": "dist_code",  # 所在鄉鎮市區代碼
            "route": "route",  # 道路
            "crossoverobject": "crossover_route",  # 跨越道路
            "adopt_status": "adopt_status",  # 認養情況
            "designengineers": "design_engineers",  # 設計單位
            "superviseengineers": "supervise_engineers",  # 監造單位
            "buildengineers": "build_engineers",  # 施工單位
            "length": "total_length_meters",  # 地下道總長m
            "area": "area_square_meters",  # 總投影面積m2
            "length1": "main_structure_length_meters",  # 主通道結構體長度m
            "length2": "sub_structure_length_meters",  # 出入口副通道/引道長度m
            "maxwidth": "max_width_meters",  # 最大淨寬m
            "minwidth": "min_width_meters",  # 最小淨寬m
            "upheight": "main_structure_min_height_meters",  # 主通道最小淨高m
            "driveway": "drive_way_count",  # 總車道數車行專用
            "Obj_Longitude": "obj_longitude",  # 代表點經度(非屬出入口清單任一點，應為中心點)
            "Obj_Latitude": "obj_latitude",  # 代表點緯度(非屬出入口清單任一點，應為中心點)
            "exits": "exits",  # 出入口清單
        }
    )
    # define column type
    data["city_code"] = data["city_code"].astype(int)
    data["dist_code"] = data["dist_code"].astype(int)
    numeric_cols = [
        "total_length_meters",
        "area_square_meters",
        "main_structure_length_meters",
        "sub_structure_length_meters",
        "max_width_meters",
        "min_width_meters",
        "main_structure_min_height_meters",
        "drive_way_count",
    ]
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce")
    # process exits
    data["exit_count"] = data["exits"].apply(len)
    data["exist_list"] = data["exits"].astype(str)
    # time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # geometry
    # The ideal representation for nethers would be either polygons or linestrings. However, the
    # data source only provides a list of exit points; the actual nether geometry is not provided
    # and cannot be reconstructed from these exit points. Therefore, we utilize (Obj_Longitude,
    # Obj_Latitude), which seems the centroid of the nether, as the geometry of the nether.
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["obj_longitude"], data["obj_latitude"], from_crs=FROM_CRS
    )
    gdata = gdata.drop(columns="geometry")
    # select columns
    ready_data = gdata[
        [
            "data_time",
            "nether_id",
            "nether_kind",
            "city_code",
            "dist_code",
            "nether_name",
            "route",
            "crossover_route",
            "adopt_status",
            "admin_unit",
            "design_engineers",
            "supervise_engineers",
            "build_engineers",
            "total_length_meters",
            "area_square_meters",
            "max_width_meters",
            "min_width_meters",
            "main_structure_length_meters",
            "main_structure_min_height_meters",
            "sub_structure_length_meters",
            "drive_way_count",
            "exit_count",
            "exist_list",
            "lng",
            "lat",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0076")
dag.create_dag(etl_func=_R0076)
