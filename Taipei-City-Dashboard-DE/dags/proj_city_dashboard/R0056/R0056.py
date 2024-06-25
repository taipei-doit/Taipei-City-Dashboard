from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0056(**kwargs):
    import geopandas as gpd
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import (
        convert_geometry_to_wkbgeometry,
        convert_polygon_to_multipolygon,
    )

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://tpland.blob.core.windows.net/blobfs/publand.csv"
    filename = f"{dag_id}.csv"
    ENCODING = "cp950"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "MultiPolygon"

    # Extract
    csv_file = download_file(filename, URL, is_proxy=True)
    raw_data = pd.read_csv(csv_file, encoding=ENCODING, encoding_errors="replace")

    # Transform
    data = raw_data.copy()
    # rename column
    data = data.rename(
        columns={
            "管理機關": "publand_1_管理機關",
            "土地權屬情形": "publand_1_土地權屬情形",
            "面積": "area",
        }
    )
    # add column
    data["publand_1_類型"] = "臺北市公有土地"
    data["cadastral map_key_地籍圖key值"] = data["段小段"] + data["地號"].astype(
        str
    ).str.zfill(8)
    # join cadastral map to get point geometry by key
    # get cadastral map data
    engine = create_engine(ready_data_db_uri)
    sql = """
        SELECT thekey, thename, thelink, aa48, aa49, aa10, aa21, 
            aa22, kcnt, cada_text, aa17, aa16, aa46, 
            ST_AsText(wkb_geometry) as geometry 
        FROM building_cadastralmap
    """
    cadastral = pd.read_sql(sql, con=engine)
    cadastral["cadastral map_key_地籍圖key值"] = cadastral["kcnt"] + cadastral["aa49"]
    cadastral["geometry"] = gpd.GeoSeries.from_wkt(
        cadastral["geometry"], crs=f"EPSG:{FROM_CRS}"
    )
    # join table
    join_data = data.merge(cadastral, how="left", on="cadastral map_key_地籍圖key值")
    # standardize geometry
    gdata = gpd.GeoDataFrame(join_data, geometry="geometry", crs=f"EPSG:{FROM_CRS}")
    gdata["geometry"] = gdata["geometry"].apply(convert_polygon_to_multipolygon)
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    # select columns
    ready_data = gdata[
        [
            "thekey",
            "thename",
            "thelink",
            "aa48",
            "aa49",
            "aa10",
            "aa21",
            "aa22",
            "kcnt",
            "cada_text",
            "aa17",
            "aa16",
            "aa46",
            "cadastral map_key_地籍圖key值",
            "publand_1_類型",
            "publand_1_土地權屬情形",
            "publand_1_管理機關",
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
    update_lasttime_in_data_to_dataset_info(engine, dag_id)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0056")
dag.create_dag(etl_func=_R0056)
