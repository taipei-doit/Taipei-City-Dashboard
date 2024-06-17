from airflow import DAG
from operators.build_common_dag import BuildCommonDagOperator
from settings.defaults import IS_PRD

PROJ_FOLDER = "proj_city_dashboard"


def _transfer_to_db_D070301(**kwargs):
    """
    商圈基本資料
    comm_shopping_area_profile
    comm_shopping_area_profile_history
    """
    import geopandas as gpd
    import pandas as pd
    import requests
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from geoalchemy2 import Geometry
    from shapely.geometry import Polygon
    from sqlalchemy import create_engine
    from sqlalchemy.sql import text as sa_text
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    from utils.get_time import get_tpe_now_time_str

    def _preprocess_geometry(single_coneregs):
        coordinates = [(item["x"], item["y"]) for item in single_coneregs]
        polygon = Polygon(coordinates)
        return polygon

    # Config
    psql_uri = PostgresHook(postgres_conn_id="postgres_default").get_uri()
    psql_table = kwargs.get("psql_table", None)
    history_table = kwargs.get("history_table", None)
    url = "https://tcdbbg.gov.taipei/api/businessdistrict/"
    col_map = {
        "code": "id",
        "district": "dist",
        "organname": "organ_name",
    }
    keep_col = ["id", "dist", "name", "organ_name", "location", "mrt", "wkb_geometry"]

    # ET
    district_code = 1
    results = []
    while True:
        district_url = url + str(district_code)
        response = requests.get(district_url, timeout=60)
        if response.status_code == 200:
            res_json = response.json()
            results.append(res_json)
        elif response.status_code == 500:
            print("Could not find district!")
            print(f"URL: {district_url}, status code: {response.status_code}")
            break
        else:
            print("Request failed!")
            print(f"URL: {district_url}, status code: {response.status_code}")
            break
        district_code += 1
    data = pd.DataFrame(results)
    # process geometry
    geometry = data["cONERGPs"].apply(_preprocess_geometry)
    gdata = gpd.GeoDataFrame(data, geometry=geometry, crs="EPSG:4326")
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs="EPSG:4326")
    # reshape
    gdata.rename(columns=col_map, inplace=True)
    gdata = gdata[keep_col]

    # Save data
    engine = create_engine(psql_uri)
    engine.execute(
        sa_text(f"TRUNCATE TABLE {psql_table}").execution_options(autocommit=True)
    )
    gdata.to_sql(
        psql_table,
        engine,
        if_exists="append",
        index=False,
        schema="public",
        dtype={"wkb_geometry": Geometry("Point", srid=4326)},
    )
    gdata.to_sql(
        history_table,
        engine,
        if_exists="append",
        index=False,
        schema="public",
        dtype={"wkb_geometry": Geometry("Point", srid=4326)},
    )

    # Drop duplicates
    # No need

    # Update datasest_info
    lasttime_in_data = get_tpe_now_time_str()
    sql = f"""
        UPDATE dataset_info 
        SET lasttime_in_data =  TO_TIMESTAMP('{lasttime_in_data}', 'yyyy-MM-dd hh24:mi:ss') 
        WHERE airflow_dag_id = 'D070301'
        """
    engine.execute(sql)


dag = BuildCommonDagOperator.create_dag(
    "D070301", IS_PRD, PROJ_FOLDER, _transfer_to_db_D070301
)
