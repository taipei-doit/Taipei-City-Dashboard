from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0042(**kwargs):
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
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
    URL = "https://data.taipei/api/frontstage/tpeod/dataset.view?id=0554bac7-cbc2-4ef3-a55e-0aad3dd4ee1d"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    # reqest file list
    res = requests.get(URL)
    if res.status_code != 200:
        raise ValueError(f"Failed to get data from {URL}")
    res_json = res.json()
    # extract all files
    temps = []
    for item in res_json["payload"]["resources"]:
        encoding = item["encoding"]
        rid = item["rid"]
        URL = f"https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid={rid}"
        last_modified = item["last_modified"]
        file_name = item["file_name"]
        # read csv
        try:
            temp = pd.read_csv(URL, encoding=encoding)
        except UnicodeDecodeError:
            temp = pd.read_csv(URL, encoding="cp950")
        temp["file_name"] = file_name
        temp["data_time"] = last_modified
        temps.append(temp)
    raw_data = pd.concat(temps)

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(columns={"處理別": "type", "肇事地點": "location"})
    # time
    data["發生時間"] = data["發生時間"].str.replace('"', "").str.replace("-", " ")
    data["occur_time"] = convert_str_to_time_format(data["發生時間"])
    data["epoch_time"] = data["occur_time"].apply(
        lambda x: x.timestamp() if not pd.isna(x) else None
    )
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, data["座標-X"], data["座標-Y"], from_crs=FROM_CRS
    )
    # select columns
    ready_data = gdata[["occur_time", "type", "location", "wkb_geometry", "epoch_time"]]

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
    lasttime_in_data = data["occur_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0042")
dag.create_dag(etl_func=_R0042)
