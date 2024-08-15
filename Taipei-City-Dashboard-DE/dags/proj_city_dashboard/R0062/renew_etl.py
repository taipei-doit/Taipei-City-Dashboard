# R0062, R0063, R0064, R0065, R0066
def renew_etl(url, from_crs, geometry_type, **kwargs):
    import geopandas as gpd
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
    raw_data = gpd.read_file(local_file, from_crs=from_crs, driver="GeoJSON")
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
