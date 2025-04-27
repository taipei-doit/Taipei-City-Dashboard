import re
from airflow import DAG
from operators.common_pipeline import CommonDag
from utils.load_stage import save_dataframe_to_postgresql,update_lasttime_in_data_to_dataset_info
from sqlalchemy import create_engine, text
import pandas as pd
import requests
from utils.get_time import get_tpe_now_time_str
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta, timezone # Import datetime components
import json # Import json for components
import random, string  # 新增：用於產生亂碼


def _transfer(**kwargs):

    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    # 連接到來源資料庫
    data_engine = create_engine(ready_data_db_uri)
    damage_case_table = "eoc_damage_case_tpe"
    disaster_summary_table = "eoc_disaster_summary_tpe"
    pname = None # 初始化 pname

    try:
        with data_engine.connect() as connection:
            # --- 合併兩表 distinct pname（24h 內），只取第一筆 ---
            names_sql = text(f"""
                SELECT DISTINCT name
                  FROM (
                       SELECT dp_name AS name
                         FROM {damage_case_table}
                        WHERE data_time >= NOW() - INTERVAL '24 hours'
                       UNION ALL
                       SELECT dpname AS name
                         FROM {disaster_summary_table}
                        WHERE data_time >= NOW() - INTERVAL '24 hours'
                   ) t
            """)
            unique_names = [row[0] for row in connection.execute(names_sql).fetchall()]

            # 無資料：刪除關聯並結束
            if not unique_names:
                print("無需更新儀表板，24h 內無資料，移除關聯。")
                dashboard_hook = PostgresHook(postgres_conn_id="dashboad-postgre")
                dashboard_hook.run(
                    "DELETE FROM public.dashboard_groups "
                    "WHERE dashboard_id = %(dashboard_id)s AND group_id = %(group_id)s;",
                    parameters={'dashboard_id': 16, 'group_id': 171}
                )
                print("已刪除 dashboard_groups 關聯。")
                return

            # 有資料：更新 dashboards & 插入關聯
            pname = unique_names[0] if len(unique_names) == 1 else "EOC開設(綜合)"
            print(f"處理後的 pname: {pname}")
            dashboard_hook = PostgresHook(postgres_conn_id="dashboad-postgre")
            # 更新 dashboards
            dashboard_hook.run(
                "UPDATE public.dashboards SET name = %(name)s WHERE id = %(id)s;",
                parameters={'name': pname, 'id': 16}
            )
            print("已更新 dashboards 名稱。")
            # 插入 dashboard_groups
            dashboard_hook.run(
                "INSERT INTO public.dashboard_groups (dashboard_id, group_id) "
                "VALUES (%(dashboard_id)s, %(group_id)s) ON CONFLICT DO NOTHING;",
                parameters={'dashboard_id': 16, 'group_id': 171}
            )
            print("已插入 dashboard_groups 關聯。")

            # ...existing component/chart 建立或其他邏輯...

    except Exception as e:
        print(f"執行過程中發生錯誤: {e}")
        raise

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='eoc_dashboard_controller')
dag.create_dag(etl_func=_transfer)
