from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0020(**kwargs):
    from sqlalchemy import create_engine
    from utils.extract_stage import get_shp_file
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import (
        convert_geometry_to_wkbgeometry,
        convert_linestring_to_multilinestring,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=e7a23ebc-f56b-424f-8073-f2469dc99c6d"
    FROM_CRS = 3826
    ENCODING = "UTF-8"
    GEOMETRY_TYPE = "MultiLineStringZ"

    # extract
    raw_data = get_shp_file(URL, dag_id, FROM_CRS, encoding=ENCODING)
    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Transform
    gdata = raw_data.copy()
    # rename
    gdata.columns = gdata.columns.str.lower()
    # standardize time
    gdata["data_time"] = convert_str_to_time_format(gdata["data_time"])
    # standardize geometry
    gdata["geometry"] = gdata["geometry"].apply(convert_linestring_to_multilinestring)
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    # secelt columns
    ready_data = gdata[
        [
            "msisid",
            "level",
            "url",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0020")
dag.create_dag(etl_func=_R0020)
