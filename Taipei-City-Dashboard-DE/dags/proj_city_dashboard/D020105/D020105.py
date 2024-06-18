from airflow import DAG
from operators.common_pipeline import CommonDag


def _D020105(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_address import (
        clean_data,
        get_addr_xy_parallel,
        main_process,
        save_data,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID = "e7aecde4-ef04-46e3-849b-1ee159ea6d5f"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    raw_list = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(raw_list)
    raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "地址": "address",
            "面積": "area",
            "容留人數": "person_capacity",
            "無障礙設施": "is_accessible",
            "data_time": "data_time",
        }
    )
    # drop wierd rows
    data = data.dropna(subset="area")
    # define columns
    data["area"] = pd.to_numeric(data["area"], errors="coerce")
    data["person_capacity"] = pd.to_numeric(data["person_capacity"], errors="coerce")
    # convert to bool
    data["is_accessible"] = data["is_accessible"].apply(
        lambda x: True if x == "有" else False
    )
    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # geocoding
    addr = data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    data["address"] = output
    unique_addr = pd.Series(output.unique())
    x, y = get_addr_xy_parallel(unique_addr)
    temp = pd.DataFrame({"lng": x, "lat": y, "address": unique_addr})
    data = pd.merge(data, temp, on="address", how="left")
    # add town
    town_pattern = "(中正|大同|中山|松山|大安|萬華|信義|士林|北投|內湖|南港|文山)區"
    data["town"] = data["address"].str.extract(town_pattern, expand=False) + "區"
    data.loc[data["town"] == "區", "town"] = ""
    # define columns
    data["lng"] = pd.to_numeric(data["lng"], errors="coerce")
    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["lng"], data["lat"], from_crs=FROM_CRS
    )
    # select columns
    ready_data = gdata[
        [
            "data_time",
            "town",
            "address",
            "area",
            "person_capacity",
            "is_accessible",
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
    lasttime_in_data = data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D020105")
dag.create_dag(etl_func=_D020105)
