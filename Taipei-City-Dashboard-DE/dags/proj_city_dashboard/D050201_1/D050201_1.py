from airflow import DAG
from operators.common_pipeline import CommonDag


def _D050201_1(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_json_file
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
    URL = "https://tppkl.blob.core.windows.net/blobfs/TaipeiTree.json"
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # Extract
    raw_data = get_json_file(
        URL, dag_id, timeout=None, is_proxy=True, output_format="dataframe"
    )

    # Transform
    data = raw_data.copy()
    # rename
    data.columns = data.columns.str.lower()
    data = data.rename(
        columns={
            "treeid": "name",
            "dist": "dist",
            "region": "region",  # 路段位置
            "regionremark": "region_ps",  # 路段備註
            "treetype": "type",  # 樹種
            "diameter": "diameter",  # 樹胸徑
            "treeheight": "height",  # 樹高
            "surveydate": "survey_date",  # 調查日期
            "upddate": "data_time",  # 更新日期
            "twd97x": "lng",
            "twd97y": "lat",
        }
    )
    # define column type
    data["diameter"] = pd.to_numeric(data["diameter"], errors="coerce")
    data["height"] = pd.to_numeric(data["height"], errors="coerce")
    data["lng"] = pd.to_numeric(data["lng"], errors="coerce")
    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    # time
    data["data_time"] = convert_str_to_time_format(
        data["data_time"], output_level="date"
    )
    data["survey_date"] = convert_str_to_time_format(
        data["survey_date"], output_level="date"
    )
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    # Reshape
    ready_data = gdata[
        [
            "data_time",
            "name",
            "dist",
            "region",
            "region_ps",
            "type",
            "diameter",
            "height",
            "survey_date",
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
    lasttime_in_data = gdata["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D050201_1")
dag.create_dag(etl_func=_D050201_1)
