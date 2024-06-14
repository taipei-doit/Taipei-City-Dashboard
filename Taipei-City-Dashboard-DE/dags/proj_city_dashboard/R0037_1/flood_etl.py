from airflow import DAG


def flood_etl(url, page_rank, **kwargs):
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_file_last_modified_time, get_kml
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    FROM_CRS = 4326
    PAGE_ID = "fa1e8012-ebb4-473b-888e-97f9a9ce365e"
    GEOMETRY_TYPE = "MultiPolygonZ"

    # Extract
    raw_data = get_kml(url, dag_id, FROM_CRS)
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(
        PAGE_ID, rank=page_rank
    )

    # Transform
    gdata = raw_data.copy()
    # rename
    gdata.columns = gdata.columns.str.lower()
    gdata = gdata.rename(
        columns={
            "name": "name",
            "description": "description",
            "data_time": "data_time",
            "geometry": "geometry",
        }
    )
    # add area
    gdata = gdata.to_crs(epsg=3826)
    gdata["area"] = gdata["geometry"].apply(lambda x: x.area).round()
    # standarlize time
    gdata["data_time"] = convert_str_to_time_format(gdata["data_time"])
    # standarlize geometry
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=3826)
    # select column
    ready_data = gdata[
        [
            "data_time",
            "name",
            "area",
            "description",
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
