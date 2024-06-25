from airflow import DAG
from operators.common_pipeline import CommonDag


# R0018
def _R0018(**kwargs):
    import os

    import geopandas as gpd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        download_file,
        unzip_file_to_target_folder,
    )
    from utils.load_stage import (
        drop_duplicated_after_saving,
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
    filename = f"{dag_id}.zip"
    unzip_path = f"{data_path}/{dag_id}"
    URL = r"https://data.moa.gov.tw/OpenData/GetOpenDataFile.aspx?id=I88&FileType=SHP&RID=27237"
    FILE_ENCODING = "UTF-8"
    FROM_CRS = 3826
    GEOMETRY_TYPE = "MultiLineString"

    # Extract
    zip_file = download_file(filename, URL, is_proxy=True)
    unzip_file_to_target_folder(zip_file, unzip_path)
    target_shp_file = [f for f in os.listdir(unzip_path) if f.endswith("shp")][0]
    raw_data = gpd.read_file(f"{unzip_path}/{target_shp_file}", encoding=FILE_ENCODING)

    # Transform
    gdata = raw_data.copy()
    # rename
    gdata.columns = gdata.columns.str.lower()
    gdata.rename(columns={"r_area_": "r_area"}, inplace=True)
    # geometry
    # there some linestring and multilinestring in geometry column, convert them all to multilinestring
    gdata["geometry"] = gdata["geometry"].apply(convert_linestring_to_multilinestring)
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    gdata.drop(columns=["geometry"], inplace=True)
    # time
    gdata["date"] = convert_str_to_time_format(gdata["date"], from_format="%Y%m%d")
    ready_data = gdata

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

    lasttime_in_data = gdata["date"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)

    drop_duplicated_after_saving(
        engine,
        psql_table=history_table,
        criterion="AND a.debrisno = b.debrisno",
        comparing_col="ogc_fid",
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0018")
dag.create_dag(etl_func=_R0018)
