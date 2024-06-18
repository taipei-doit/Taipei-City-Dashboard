from airflow import DAG
from operators.common_pipeline import CommonDag


def today_road_use_etl(url, **kwargs):
    import geopandas as gpd
    import pandas as pd
    from geopandas.tools import sjoin
    from shapely import wkt
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import (
        convert_geometry_to_wkbgeometry,
        convert_twd97_to_wgs84,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    GEOMETRY_TYPE = "Polygon"
    file_name = f"{dag_id}.geojson"
    FROM_CRS = 3826
    if url.endswith("TodayRallyCase.json"):
        code_column_name = "ral_code"
        key_word = "ral"
    elif url.endswith("TodayUrgentCase.json"):
        code_column_name = "bill_code"
        key_word = "urgent"

    # Extract
    local_file = download_file(file_name, url, is_proxy=True)
    raw_data = gpd.read_file(local_file, driver="GeoJSON")
    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Transform
    gdata = raw_data.copy()
    # rename
    gdata.columns = gdata.columns.str.lower()
    gdata = gdata.rename(
        columns={
            code_column_name: "bill_code",
            f"{key_word}_rcv_date": "recieve_date",
            f"{key_word}_start_date": "start_date",
            f"{key_word}_end_date": "end_date",
            f"{key_word}_address1": "address_1",
            "x1": "lng_twd97_1",
            "y1": "lat_twd97_1",
            f"{key_word}_address2": "address_2",
            "x2": "lng_twd97_2",
            "y2": "lat_twd97_2",
            "data_time": "data_time",
            "geometry": "geometry",
        }
    )
    # define column type
    str_cols = [
        "bill_code",
        "recieve_date",
        "start_date",
        "end_date",
        "address_1",
        "address_2",
        "data_time",
    ]
    for col in str_cols:
        gdata[col] = gdata[col].astype(str)

    num_cols = ["lng_twd97_1", "lat_twd97_1", "lng_twd97_2", "lat_twd97_2"]
    for col in num_cols:
        gdata[col] = pd.to_numeric(gdata[col], errors="coerce")

    # standardize time
    gdata["data_time"] = convert_str_to_time_format(gdata["data_time"])
    gdata["recieve_date"] = convert_str_to_time_format(
        gdata["recieve_date"], from_format="%Y%m%d"
    )
    gdata["start_date"] = convert_str_to_time_format(
        gdata["start_date"], from_format="%Y%m%d%H%M%S"
    )
    gdata["end_date"] = convert_str_to_time_format(
        gdata["end_date"], from_format="%Y%m%d%H%M%S"
    )
    # standardize geometry
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    gdata["lng_1"], gdata["lat_1"] = convert_twd97_to_wgs84(
        gdata, x_col="lng_twd97_1", y_col="lat_twd97_1"
    )
    gdata["lng_2"], gdata["lat_2"] = convert_twd97_to_wgs84(
        gdata, x_col="lng_twd97_2", y_col="lat_twd97_2"
    )
    # use address 1 to add district
    # read district
    engine = create_engine(ready_data_db_uri)
    sql = "SELECT tname, ST_ASTEXT(wkb_geometry) AS geometry FROM tp_district"
    district = pd.read_sql(sql, engine)
    district["geometry"] = district["geometry"].apply(wkt.loads)
    district = gpd.GeoDataFrame(district, geometry="geometry", crs="EPSG:4326")
    # select point data
    point_data = gdata[["bill_code", "lng_1", "lat_1"]]
    point_gdata = gpd.GeoDataFrame(
        point_data,
        geometry=gpd.points_from_xy(x=point_data["lng_1"], y=point_data["lat_1"]),
    )
    # merge
    point_within_district = sjoin(point_gdata, district, how="left", op="within")
    gdata = gdata.merge(
        point_within_district[["bill_code", "tname"]], on="bill_code", how="left"
    )
    # select column
    gdata.rename(columns={"tname": "dist"}, inplace=True)
    ready_data = gdata[
        [
            "data_time",
            "bill_code",
            "recieve_date",
            "start_date",
            "end_date",
            "dist",
            "address_1",
            "lng_1",
            "lat_1",
            "address_2",
            "lng_2",
            "lat_2",
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
