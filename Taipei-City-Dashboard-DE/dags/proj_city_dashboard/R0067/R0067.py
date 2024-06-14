from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0067(**kwargs):
    import geopandas as gpd
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        drop_duplicated_after_saving,
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_address import clean_data, transfer_land_num
    from utils.transform_geometry import (
        convert_geometry_to_wkbgeometry,
        convert_polygon_to_multipolygon,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_folder = kwargs.get("data_folder")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID = "15c3dde7-b6db-4a66-84c2-098236b84512"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "MultiPolygon"

    # Extract
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "管理機關": "10712土地_1_管理機關",
        }
    )
    # data time
    data["data_time"] = data["_importdate"].apply(lambda x: x["date"])
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # extract string
    data["段代碼"] = data["段代碼_段小段_地號"].str.split("_").str.get(0)
    data["段小段"] = data["段代碼_段小段_地號"].str.split("_").str.get(1)
    data["段小段"] = clean_data(data["段小段"])
    data["地號"] = data["段代碼_段小段_地號"].str.split("_").str.get(2)
    data["地號"] = data["地號"].apply(transfer_land_num)
    data["cadastral map_key_地籍圖key值"] = data["段小段"] + data["地號"]
    # read building_cadastralmap for geometry mapping
    sql = """
        SELECT thekey, thename, thelink, aa48, aa49, aa10, aa21, 
            aa22, kcnt, cada_text, aa17, aa16, aa46, 
            ST_AsText(wkb_geometry) as geometry 
        FROM building_cadastralmap
    """
    engine = create_engine(ready_data_db_uri)
    cadastral = pd.read_sql(sql, con=engine)
    cadastral["aa49"] = cadastral["aa49"].astype(str)
    cadastral["cadastral map_key_地籍圖key值"] = cadastral["kcnt"] + cadastral["aa49"]
    cadastral["geometry"] = gpd.GeoSeries.from_wkt(
        cadastral["geometry"], crs=f"EPSG:{FROM_CRS}"
    )
    # join geometry
    join_data = data.merge(cadastral, how="inner", on="cadastral map_key_地籍圖key值")
    # standardize geometry
    gdata = gpd.GeoDataFrame(join_data, geometry="geometry", crs=f"EPSG:{FROM_CRS}")
    gdata["geometry"] = gdata["geometry"].apply(convert_polygon_to_multipolygon)
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    # calculate area
    gdata["area"] = pd.to_numeric(gdata["面積_m2"])
    # select columns
    ready_data = gdata[
        [
            "data_time",
            "thekey",
            "thename",
            "thelink",
            "aa48",
            "aa49",
            "aa10",
            "aa21",
            "kcnt",
            "cada_text",
            "aa17",
            "aa16",
            "aa46",
            "cadastral map_key_地籍圖key值",
            "10712土地_1_管理機關",
            "area",
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
    drop_duplicated_after_saving(
        engine,
        psql_table=history_table,
        criterion="AND a.thekey = b.thekey",
        comparing_col="ogc_fid",
    )
    update_lasttime_in_data_to_dataset_info(engine, airflow_dag_id=dag_id)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0067")
dag.create_dag(etl_func=_R0067)
