from airflow import DAG


def green_land_etl(green_land_type, url, page_rank, geometry_type, **kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        get_data_taipei_file_last_modified_time,
        get_geojson_file,
    )
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import (
        convert_geometry_to_wkbgeometry,
        convert_polygon_to_multipolygon,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    PAGE_ID = "5b277432-f534-4d09-a24c-d3f6b514e042"
    FROM_CRS = 3826

    # Extract
    raw_data = get_geojson_file(url, dag_id, FROM_CRS)
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(
        PAGE_ID, rank=page_rank
    )

    # Transform
    gdata = raw_data.copy()
    # colname
    gdata.columns = gdata.columns.str.lower()
    gdata = gdata.rename(
        columns={
            "id": "id",
            "名稱": "name",
            "面積": "area",
            "體積": "volume",
            "圖形": "geometry_type",
            "geometry": "geometry",
        }
    )
    # special case for D050303_2
    # drop all linestring, cause they looks like error data
    # make all point to multipolygon
    if green_land_type == "校園綠化":
        gdata = gdata.loc[gdata["geometry_type"] != "線"]
        # make all point to multipolygon
        is_point = gdata["geometry_type"] == "點"
        gdata.loc[is_point, "geometry"] = gdata.loc[is_point, "geometry"].buffer(10)
        gdata.loc[is_point, "geometry"] = gdata.loc[is_point, "geometry"].apply(
            convert_polygon_to_multipolygon
        )
    # define column type
    gdata["area"] = pd.to_numeric(gdata["area"], errors="coerce")
    gdata["area"] = gdata["geometry"].apply(lambda x: x.area)
    # add type
    gdata["type"] = green_land_type
    # time
    gdata["data_time"] = convert_str_to_time_format(gdata["data_time"])
    # geometry
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    # select column
    ready_data = gdata[
        [
            "data_time",
            "id",
            "type",
            "name",
            "area",
            "wkb_geometry",
        ]
    ]

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=geometry_type,
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)
