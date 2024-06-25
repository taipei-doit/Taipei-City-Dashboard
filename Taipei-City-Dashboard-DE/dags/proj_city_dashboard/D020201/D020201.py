from airflow import DAG
from operators.common_pipeline import CommonDag


def _D020201(**kwargs):
    import geopandas as gpd
    import pandas as pd
    from shapely import wkt
    from shapely.ops import unary_union
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_address import clean_data
    from utils.transform_geometry import (
        convert_geometry_to_wkbgeometry,
        convert_linestring_to_multilinestring,
    )
    from utils.transform_time import convert_str_to_time_format

    def _show_wired_addr(street_data):
        addr_level = ['弄', '巷', '街', '段', '橋', '路']
        for addr in street_data:
            if addr[-1] in addr_level:
                pass
            else:
                print(addr)

    def _union_geometries(geometries):
        return unary_union(geometries.tolist())

    def _show_unmatched_street(geo_data_frame):
        is_unmatched = geo_data_frame["town"].isna()
        print(geo_data_frame.loc[is_unmatched, 'street'])

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID = "cd4ec60e-8d53-48a5-bbf1-9ec1f2afc20b"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "MultiLineString"

    # Extract
    raw_list = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(raw_list)
    raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "分類": "type",
            "行政區代碼": "dist_code",
            "分隊名稱": "fire_brigade",
            "巷道名稱": "street",
            "寬度（公尺）": "width_meter",
            "備註": "note",
            "data_time": "data_time",
        }
    )
    # define columns type
    data["width_meter"] = data["width_meter"].astype(float)
    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # truncate street to vally level
    data["street"] = clean_data(data["street"])
    data["street"] = data["street"].str.split("(", expand=True)[0]
    data["street"] = data["street"].str.split("（", expand=True)[0]
    data["street"] = data["street"].str.replace("橋下", "橋")
    data["street"] = data["street"].str.replace("號前", "號")
    # _show_wired_addr(data["street"])
    # merge lane geometry
    # read lane geometry
    engine = create_engine(ready_data_db_uri)
    sql = """
        SELECT 
            roadid AS road_id,
            county,
            district AS town,
            COALESCE(britunname, '') AS bridge,
            COALESCE(roadname, '') || 
            COALESCE(rdnamesect, '') || 
            COALESCE(rdnamelane, '') || 
            COALESCE(rdnamenon, '') AS street,
            ST_ASTEXT(wkb_geometry) AS geometry
        FROM public.tp_road_center_line
    """
    street = pd.read_sql(sql, engine)
    is_bridge = street["bridge"] != ""
    street.loc[is_bridge, "street"] = street.loc[is_bridge, "bridge"]
    street = street.loc[(street["street"] != "") & (street["street"] != "無名")]
    street["geometry"] = street["geometry"].apply(wkt.loads)
    # union multiple geometry because one lane_name can have multiple geometry
    street_agg = street.groupby(["county", "town", "street"]).agg(
        {"geometry": _union_geometries}
    )
    street_agg = street_agg.reset_index()
    # merge by street name. ! 45/283 rows are not matched
    gdata = data.merge(street_agg, on="street", how="left")
    # standardize geometry
    gdata = gpd.GeoDataFrame(gdata, geometry="geometry", crs=f"EPSG:{FROM_CRS}")
    gdata["geometry"] = gdata["geometry"].apply(convert_linestring_to_multilinestring)
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    _show_unmatched_street(gdata)
    # select columns
    ready_data = gdata[
        [
            "data_time",
            "type",
            "fire_brigade",
            "county",
            "town",
            "street",
            "width_meter",
            "note",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D020201")
dag.create_dag(etl_func=_D020201)
