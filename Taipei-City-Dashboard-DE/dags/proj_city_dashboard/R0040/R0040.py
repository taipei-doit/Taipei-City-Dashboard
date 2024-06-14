from airflow import DAG
from operators.common_pipeline import CommonDag


def _correct_4_digit_year_to_3_digit(time_column):
    time_column = time_column.astype(str)
    is_4_digit_year = len(time_column.iloc[0].split("-")[0]) == 4
    if is_4_digit_year:
        time_column = time_column.str.slice(
            1,
        )
    return time_column


def _R0040(**kwargs):
    import json

    import geopandas as gpd
    from shapely.geometry import shape
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
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
    URL = "https://tpnco.blob.core.windows.net/blobfs/Todaywork.json"
    FILE_NAME = "Todaywork.json"
    FROM_CRS = 3826
    GEOMETRY_TYPE = "Point"

    # Extract
    local_file = download_file(FILE_NAME, URL, is_proxy=True)
    # Use gpd.read_file got error `ValueError: day is out of range for month`.
    # Which is caused by fiona, and very hard to fix.
    # So use json.load to read file and then process it to gpd.GeoDataFrame.
    with open(local_file, "r", encoding="utf-8-sig") as f:
        res = json.load(f, strict=False)
    geometries = [shape(feature["geometry"]) for feature in res["features"]]
    properties = [feature["properties"] for feature in res["features"]]
    raw_data = gpd.GeoDataFrame(properties, crs=f"EPSG:{FROM_CRS}", geometry=geometries)

    # Transform
    gdata = raw_data.copy()
    # rename
    gdata.columns = gdata.columns.str.lower()
    # define column type
    gdata["isstay"] = gdata["isstay"].replace({"是": True, "否": False})
    gdata["isblock"] = gdata["isblock"].replace({"是": True, "否": False})
    # positions column in DB is JSON type
    gdata["positions"] = gdata["positions"].apply(lambda x: json.dumps(x))
    # time
    # apptime = 通報時間
    gdata["apptime"] = _correct_4_digit_year_to_3_digit(gdata["apptime"])
    gdata["apptime_ad"] = convert_str_to_time_format(
        gdata["apptime"], from_format="%TY-%m-%dT%H:%M:S"
    )
    # cb_da = 核准施工起日
    gdata["cb_da"] = _correct_4_digit_year_to_3_digit(gdata["cb_da"])
    gdata["cb_ad"] = convert_str_to_time_format(
        gdata["cb_da"], from_format="%TY-%m-%d", output_level="date"
    )
    # ce_da = 核准施工迄日
    gdata["ce_da"] = _correct_4_digit_year_to_3_digit(gdata["ce_da"])
    gdata["cd_ad"] = convert_str_to_time_format(
        gdata["ce_da"], from_format="%TY-%m-%d", output_level="date"
    )
    # geometry
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    ready_data = gdata.drop(columns=["geometry"])

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
    lasttime_in_data = gdata["apptime_ad"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0040")
dag.create_dag(etl_func=_R0040)
