from airflow import DAG
from operators.build_common_dag import BuildCommonDagOperator
from settings.defaults import IS_PRD

PROJ_FOLDER = "proj_city_dashboard"


# R0035
# ("Instant_rainfall","patrol_rain_rainfall")
def _transfer_to_db_R0035(**kwargs):
    from ast import literal_eval

    import pandas as pd
    import requests
    from airflow.models import Variable
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from geoalchemy2 import Geometry
    from sqlalchemy import create_engine
    from sqlalchemy.sql import text as sa_text
    from utils.transform_time import convert_str_to_time_format

    # Config
    psql_uri = PostgresHook(postgres_conn_id="postgres_default").get_uri()
    psql_table = kwargs.get("psql_table", None)
    history_table = kwargs.get("history_table", None)
    proxies = literal_eval(Variable.get("PROXY_URL"))
    URL = "https://wic.heo.taipei/OpenData/API/Rain/Get?stationNo=&loginId=taipeiapi&dataKey=E9A68716"

    # Get data
    response = requests.get(URL, proxies=proxies)
    res_json = response.json()
    if res_json:
        data = res_json["data"]
        df = pd.DataFrame(data)
        df["recTime"] = df["recTime"].apply(
            lambda x: (
                x[0:4] + "-" + x[4:6] + "-" + x[6:8] + " " + x[8:10] + ":" + x[10:12] + ":00"
                if x else None
            )
        )
        df["recTime"] = df["recTime"].str.replace("3022", "2022")
        df["recTime"] = df["recTime"].str.replace("2823", "2023")
        df["recTime"] = df["recTime"].str.replace("6023", "2023")
        df["rec_time"] = convert_str_to_time_format(df["recTime"])

        col_map = {
            "stationNo": "station_no",
            "stationName": "station_name",
        }
        df = df.rename(columns=col_map)

        select_col = ["station_no", "station_name", "rec_time", "rain"]
        df = df[select_col]

        # Load
        engine = create_engine(psql_uri)
        with engine.begin() as conn:
            conn.execute(
                sa_text(f"TRUNCATE TABLE {psql_table}").execution_options(
                    autocommit=True
                )
            )
            df.to_sql(
                psql_table,
                conn,
                if_exists="append",
                index=False,
                schema="public",
                dtype={"wkb_geometry": Geometry("Polygon", srid=4326)},
            )
            df.to_sql(
                history_table,
                conn,
                if_exists="append",
                index=False,
                schema="public",
                dtype={"wkb_geometry": Geometry("Polygon", srid=4326)},
            )

            # lasttimeindata
            lasttime_in_data = df["rec_time"].max()
            sql = f"""UPDATE dataset_info SET lasttime_in_data = TO_TIMESTAMP('{lasttime_in_data}', 'yyyy-MM-dd hh24:mi:ss') WHERE psql_table_name = '{psql_table}'"""
            conn.execute(sql)


dag = BuildCommonDagOperator.create_dag(
    "R0035", IS_PRD, PROJ_FOLDER, _transfer_to_db_R0035
)
