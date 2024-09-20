from airflow import DAG
from operators.build_calculate_dag import BuildCalculateDagOperator
from settings.defaults import IS_PRD

PROJ_FOLDER = "proj_city_dashboard"


# R0035 hourly
def _app_calculate_hourly_R0035(**kwargs):
    from datetime import datetime

    import pandas as pd
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from sqlalchemy import create_engine

    # Config
    psql_uri = PostgresHook(postgres_conn_id="postgres_default").get_uri()
    input_table = kwargs.get("input_table", None)
    output_table = kwargs.get("psql_table", None)
    info_table = kwargs.get("info_table", None)
    airflow_dag_id = kwargs.get("airflow_dag_id", None)

    sql = f"""
        select this_hr.station_no as station_no , this_hr.station_name as station_name, (rain - last_hr_rain) as hr_acc_rain, rain as this_hr, last_hr_rain as last_hr, rec_time,last_hr_rec_time from  (
        select distinct on (station_no) station_no,station_name,rain,rec_time from {input_table} where rec_time is not null and rec_time > now() - interval '1 hour' 
        and (station_no in (select station_no from work_rainfall_station_location) or station_no in (select station_no from cwb_rainfall_station_location where city = '臺北市')) 
        order by station_no, _ctime desc limit 1000) as this_hr 
        left join(
        select distinct on (station_no) station_no,rain as last_hr_rain, rec_time as last_hr_rec_time from {input_table} where rec_time is not null and rec_time > now() - interval '2 hour' and rec_time <= now() - interval '1 hour' and station_no in (select station_no from work_rainfall_station_location) order by station_no, _ctime desc limit 1000 
        ) as last_hr on this_hr.station_no = last_hr.station_no
    """
    engine = create_engine(psql_uri)
    df = pd.read_sql(sql, engine)
    if not df.empty:
        df.to_sql(
            output_table,
            engine,
            if_exists="append",
            index=False,
            schema="public",
            chunksize=10000,
        )
        # lasttimeindata
        lasttime_in_data = datetime.now()
        sql = f"""UPDATE {info_table} SET lasttime_in_data = TO_TIMESTAMP('{lasttime_in_data}', 'yyyy-MM-dd hh24:mi:ss') WHERE airflow_dag_id = '{airflow_dag_id}'"""
        engine.execute(sql)
    else:
        return "The data is empty, Please check"


dag = BuildCalculateDagOperator.create_dag(
    "R0035_hourly_calculate", IS_PRD, PROJ_FOLDER, _app_calculate_hourly_R0035
)
