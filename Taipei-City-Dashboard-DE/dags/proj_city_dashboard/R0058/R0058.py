from airflow import DAG
from operators.common_pipeline import CommonDag


def transform_permit_history(raw_data, from_crs, engine):
    import geopandas as gpd
    from proj_city_dashboard.R0057.R0057 import get_cadastral
    from utils.transform_geometry import (
        convert_geometry_to_wkbgeometry,
        convert_polygon_to_multipolygon,
    )
    from utils.transform_time import convert_str_to_time_format

    data = raw_data.copy()

    # rename
    data = data.rename(columns={"工程金額": "工程造價"})

    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])

    # mapping data to get geometry
    # get cadastral
    cadastral = get_cadastral(engine)
    # add merge key
    data["地段地號_key"] = data["地段地號"].str.split("區").str[1]
    data["地段地號_key"] = (
        data["地段地號_key"].str.replace("號", "").str.replace("-", "")
    )
    # join table
    join_data = data.merge(
        cadastral, how="inner", left_on="地段地號_key", right_on="key"
    )

    # standardize geometry
    join_data["geometry"] = gpd.GeoSeries.from_wkt(
        join_data["geometry"], crs=f"EPSG:{from_crs}"
    )
    gdata = gpd.GeoDataFrame(join_data, crs=f"EPSG:{from_crs}", geometry="geometry")
    gdata["geometry"] = gdata["geometry"].apply(convert_polygon_to_multipolygon)
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=from_crs)

    # rename column
    ready_data = gdata[
        [
            "地段地號",
            "地段地號_key",
            "執照年度",
            "建築地點",
            "執照號碼",
            "發照日期",
            "設計人",
            "監造人",
            "建造類別",
            "構造種類",
            "使用分區",
            "棟數",
            "地上層數",
            "地下層數",
            "戶數",
            "騎樓基地面積",
            "其他基地面積",
            "建築面積",
            "工程造價",
            "wkb_geometry",
        ]
    ]
    return ready_data


def _R0058(**kwargs):
    from proj_city_dashboard.R0057.R0057 import extarct_permit_from_xml
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
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
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=43624c8e-c768-4b3c-93c4-595f5af7a9cb"
    file_path = f"{data_path}/{dag_id}.xml"
    RID = "d8834353-ff8e-4a6c-9730-a4d3541f2669"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "MultiPolygon"

    # Extract
    raw_data = extarct_permit_from_xml(file_path, URL, RID)

    # Transform
    engine = create_engine(ready_data_db_uri)
    ready_data = transform_permit_history(raw_data, FROM_CRS, engine)

    # Load
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        geometry_type=GEOMETRY_TYPE,
    )
    lasttime_in_data = convert_str_to_time_format(
        ready_data["發照日期"], from_format="%TY%m%d"
    ).max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0058")
dag.create_dag(etl_func=_R0058)
