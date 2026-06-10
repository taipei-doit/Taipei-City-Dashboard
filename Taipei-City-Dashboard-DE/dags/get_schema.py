import os
import json
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
try:
    from airflow.hooks.base import BaseHook
    conn = BaseHook.get_connection("ready_data")
    uri = conn.get_uri()
    print("URI:", uri.replace(conn.password, "******"))
    engine = create_engine(uri)
    df = pd.read_sql("SELECT column_name, character_maximum_length FROM information_schema.columns WHERE table_name = 'tran_parking' AND data_type = 'character varying'", engine)
    print(df)
except Exception as e:
    print(e)
