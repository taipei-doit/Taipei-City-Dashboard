from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0038_2(**kwargs):
    import geopandas as gpd
    from geoalchemy2 import Geometry, WKTElement
    from sqlalchemy import create_engine
    from utils.extract_stage import get_kml
    from utils.load_stage import update_lasttime_in_data_to_dataset_info
    from utils.transform_geometry import convert_3d_polygon_to_2d_polygon
    from utils.get_time import get_tpe_now_time_str

    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_id = dag_infos.get("dag_id")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://www.ttcx.dot.gov.taipei/cpt/getLiveTrafficKML"
    FROM_CRS = 4326

    # Extract
    raw_data = get_kml(URL, dag_id, FROM_CRS)

    # Transform
    gdata = raw_data.copy()
    # rename
    col_map = {"Name": "name", "Description": "description", "geometry": "geom"}
    gdata = gdata.rename(columns=col_map)
    # add new columns
    gdata["geom"] = convert_3d_polygon_to_2d_polygon(gdata["geom"])
    gdata["snippet"] = gdata["name"]
    gdata["visibility"] = 1
    gdata["update_at"] = get_tpe_now_time_str()
    # gemetry
    gdata["geom"] = gdata["geom"].apply(
        lambda x: WKTElement(x.wkt, srid=4326) if x is not None else None
    )
    print("unique", len(gdata["name"].unique()), gdata["name"].count())

    # Load
    engine = create_engine(ready_data_db_uri)
    with engine.begin() as conn:
        for i in range(len(gdata)):
            sql = f"""
                INSERT INTO {default_table} (name, visibility, description, snippet, update_at, geom)
                VALUES (
                    '{gdata['name'][i]}',
                    1,
                    '{gdata['description'][i]}',
                    '{gdata['snippet'][i]}',
                    current_timestamp,
                    ST_geomfromtext('{gdata['geom'][i]}')
                )
                ON CONFLICT (name)
                DO
                    UPDATE SET description='{gdata['description'][i]}', update_at=current_timestamp;
            """
            conn.execute(sql)
        print(f"{default_table} update successful")
        gdata.to_sql(
            history_table,
            conn,
            if_exists="append",
            index=False,
            schema="public",
            dtype={"geom": Geometry("Polygon", srid=4326)},
        )
        print(f"{history_table} save successful")

    lasttime_in_data = gdata["update_at"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0038_2")
dag.create_dag(etl_func=_R0038_2)
