from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0054(**kwargs):
    import pandas as pd
    from settings.global_config import DAG_PATH
    from sqlalchemy import create_engine
    from utils.extract_stage import get_shp_file
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import (
        convert_geometry_to_wkbgeometry,
        convert_polygon_to_multipolygon,
    )
    from utils.transform_time import convert_str_to_time_format

    def _read_mapping_dict():
        mapping_table = pd.read_csv(
            f"{DAG_PATH}/proj_city_dashboard/R0054/land_plan_mapping_table.csv",
            encoding="utf-8",
        )
        mapping_dict = {
            row["area_code"]: row["simple_area_name"]
            for _, row in mapping_table.iterrows()
        }
        return mapping_dict

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=10196e7d-2460-4b8a-b1d2-84001d09d7a4"
    FROM_CRS = 3826
    ENCODING = "big5"
    GEOMETRY_TYPE = "MultiPolygon"

    # extract
    raw_data = get_shp_file(
        URL, dag_id, FROM_CRS, encoding=ENCODING, file_ends_with="面.shp"
    )
    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Transform
    gdata = raw_data.copy()
    # rename
    gdata = gdata.rename(
        columns={
            "編號": "id",
            "圖層": "layer",
            "顏色": "color_code",
            "街廓編號": "block_id",
            "分區代碼": "area_code",
            "分區簡稱": "area_short_name",
            "使用分區": "area_name",
            "分區說明": "area_description",
            "原屬分區": "previous_area",
            "變更前代碼": "previous_area_code",
            "變更前簡稱": "previous_area_short_name",
            "變更前分區": "previous_area_name",
            "geometry": "geometry",
        }
    )
    # define column type
    gdata["id"] = gdata["id"].astype(int)
    # standardize time
    gdata["data_time"] = convert_str_to_time_format(gdata["data_time"])
    # simplify land use type by TUIC
    mapping_dict = _read_mapping_dict()
    gdata["simple_area_name"] = gdata["area_code"].map(mapping_dict)
    # standardize geometry
    gdata["geometry"] = gdata["geometry"].apply(convert_polygon_to_multipolygon)
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    # secelt columns
    ready_data = gdata[
        [
            "data_time",
            "id",
            "layer",
            "color_code",
            "block_id",
            "simple_area_name",
            "area_code",
            "area_short_name",
            "area_name",
            "area_description",
            "previous_area",
            "previous_area_code",
            "previous_area_short_name",
            "previous_area_name",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0054")
dag.create_dag(etl_func=_R0054)
