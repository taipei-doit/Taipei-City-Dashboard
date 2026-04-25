from operators.common_pipeline import CommonDag


def _classify_facility(name: str) -> str:
    if not isinstance(name, str):
        return "other"
    if "電梯" in name:
        return "elevator"
    if "坡道" in name:
        return "ramp"
    return "other"


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        get_current_rid_from_page_id,
        get_data_taipei_api,
    )
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    PAGE_ID = "0a3bb422-9eb5-459b-a9d4-138456516183"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"
    NAME_COL = "出入口電梯/無障礙坡道名稱"

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    rid = get_current_rid_from_page_id(PAGE_ID)
    raw_list = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(raw_list)
    raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]

    data = raw_data.rename(
        columns={
            NAME_COL: "facility_name",
            "出入口編號": "exit_no",
            "經度": "lng",
            "緯度": "lat",
        }
    )
    # 從 facility_name 抽 station：「動物園站出口電梯1」→「動物園」
    data["station"] = data["facility_name"].str.extract(r"^(.+?)站", expand=False)
    data["facility_type"] = data["facility_name"].apply(_classify_facility)
    data["lng"] = pd.to_numeric(data["lng"], errors="coerce")
    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    data["data_time"] = convert_str_to_time_format(data["data_time"])

    gdata = add_point_wkbgeometry_column_to_df(
        data, data["lng"], data["lat"], from_crs=FROM_CRS
    )
    ready_data = gdata[
        [
            "station",
            "exit_no",
            "facility_name",
            "facility_type",
            "lng",
            "lat",
            "wkb_geometry",
            "data_time",
        ]
    ]

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )
    update_lasttime_in_data_to_dataset_info(
        engine, dag_id, ready_data["data_time"].max()
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="mrt_a11y_elevator")
dag.create_dag(etl_func=_transfer)
