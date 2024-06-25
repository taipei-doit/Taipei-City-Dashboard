from airflow import DAG
from operators.common_pipeline import CommonDag


def D040301_1(**kwargs):
    import json

    import pandas as pd
    from numpy import nan
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    GEOMETRY_TYPE = "Point"
    file_name = f"{dag_id}.json"
    FROM_CRS = 3826
    URL = "https://tppkl.blob.core.windows.net/blobfs/TaipeiLight.json"
    VALID_DIST = [
        "中山區",
        "中正區",
        "信義區",
        "內湖區",
        "北投區",
        "南港區",
        "士林區",
        "大同區",
        "大安區",
        "文山區",
        "松山區",
        "萬華區",
    ]

    # Extract
    local_file = download_file(file_name, URL, is_proxy=True)
    if not local_file:
        return False
    with open(local_file) as json_file:
        data = json.load(json_file)
    raw_data = pd.DataFrame(data)

    # Transform
    data = raw_data.copy()
    # rename
    data.columns = data.columns.str.lower()
    data.columns = data.columns.str.strip()
    col_map = {
        "serialnumber": "id",
        "dist": "dist",
        "quantity": "light_count",
        "lightkind1": "light1",
        "lightwatt1": "watt1",
        "lightkind2": "light2",
        "lightwatt2": "watt2",
        "lightkind3": "light3",
        "lightwatt3": "watt3",
        "lightkind4": "light4",
        "lightwatt4": "watt4",
        "lightkind5": "light5",
        "lightwatt5": "watt5",
        "lightheight": "height",
        "lightyear": "enable_year",
        "twd97x": "lng",
        "twd97y": "lat",
        "upddate": "data_time",
    }
    data = data.rename(columns=col_map)
    # define column type
    data["id"] = data["id"].astype(str)
    data["height"] = pd.to_numeric(data["height"], errors="coerce")
    data["light_count"] = pd.to_numeric(data["light_count"], errors="coerce")
    for col in data.columns:
        if col.startswith("watt"):
            is_empty = data[col] == ""
            if is_empty.sum() > 0:
                data.loc[is_empty, col] = nan
            data[col] = data[col].astype(float)
    # time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # filter invalid `enable_year`
    data["enable_year"] = pd.to_numeric(data["enable_year"], errors="coerce")
    is_chinese_year = data["enable_year"] < 1000
    is_outlier = data["enable_year"] > 10000
    data.loc[is_outlier, "enable_year"] = nan
    data.loc[is_chinese_year, "enable_year"] = (
        data.loc[is_chinese_year, "enable_year"] + 1911
    )
    # dist
    data["dist"] = data["dist"] + "區"
    # filter invalid `dist`
    data = data.loc[data["dist"].isin(VALID_DIST)]
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["lng"], data["lat"], from_crs=FROM_CRS
    )
    gdata = gdata.drop(columns=["geometry"])
    # select column
    ready_data = gdata[
        [
            "data_time",
            "id",
            "dist",
            "height",
            "enable_year",
            "lng",
            "lat",
            "wkb_geometry",
            "light_count",
            "light1",
            "watt1",
            "light2",
            "watt2",
            "light3",
            "watt3",
            "light4",
            "watt4",
            "light5",
            "watt5",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D040301_1")
dag.create_dag(etl_func=D040301_1)
