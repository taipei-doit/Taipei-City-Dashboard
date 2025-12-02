# R0062, R0063, R0064, R0065, R0066
def renew_etl(url, from_crs, geometry_type, **kwargs):
    import json
    import geopandas as gpd
    from shapely.geometry import shape
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    filename = f"{dag_id}.json"

    # Extract
    local_file = download_file(filename, url, is_verify=False)
    # 使用 json 模組讀取 GeoJSON，避免 fiona 版本問題
    with open(local_file, encoding="utf-8") as f:
        geojson_data = json.load(f)
    
    # 將 GeoJSON 轉換為 GeoDataFrame
    features = geojson_data.get("features", [])
    if features:
        rows = []
        geometries = []
        for feature in features:
            props = feature.get("properties", {})
            geom = feature.get("geometry")
            rows.append(props)
            geometries.append(shape(geom) if geom else None)
        raw_data = gpd.GeoDataFrame(rows, geometry=geometries, crs=f"EPSG:{from_crs}")
    else:
        raw_data = gpd.GeoDataFrame()
    
    if raw_data.empty:
        print("!!!GeoJSON data is empty!!!")
        return
        
    raw_data["data_time"] = get_tpe_now_time_str()

    # Transform
    gdata = raw_data.copy()
    # rename
    gdata = gdata.rename(columns={"ID": "id", "案件編號": "case_no"})
    # standardize time
    gdata["data_time"] = convert_str_to_time_format(gdata["data_time"])
    # calculate area
    gdata = gdata.to_crs("EPSG:3826")
    gdata["area"] = gdata["geometry"].area
    gdata = gdata.to_crs("EPSG:4326")
    # geometry
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=from_crs)
    # select column
    ready_data = gdata[["data_time", "id", "case_no", "area", "wkb_geometry"]]

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
    update_lasttime_in_data_to_dataset_info(engine, dag_id)
