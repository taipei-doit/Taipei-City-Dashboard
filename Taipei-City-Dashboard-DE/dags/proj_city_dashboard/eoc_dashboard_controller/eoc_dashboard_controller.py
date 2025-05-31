import re
from sqlalchemy.dialects import postgresql
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
import numpy as np
import random, string  # 新增：用於產生亂碼


def _transfer(**kwargs):

    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    # 連接到來源資料庫
    data_engine = create_engine(ready_data_db_uri)
    damage_case_table = "eoc_damage_case_tpe"
    disaster_summary_table = "eoc_disaster_summary_tpe"
    pname = None # 初始化 pname

    # try:
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
        dashboard_hook = PostgresHook(postgres_conn_id="dashboad-postgre")

        # 無資料：刪除關聯並結束
        if not unique_names:
            try:
                # 刪除所有 disaster_sus_*_% 相關的 component、query_charts、component_charts、dashboard、dashboard_groups
                dashboard_hook = PostgresHook(postgres_conn_id="dashboad-postgre")
                status_keys = ["disaster_sus_water", "disaster_sus_power", "disaster_sus_tel", "disaster_sus_gas"]
                for status_key in status_keys:
                    like_pattern = f"{status_key}_%"

                    # 1) 先處理 components：查出 id，再檢查是否仍被 dashboard 使用
                    recs = dashboard_hook.get_records(
                        'SELECT id FROM public.components WHERE "index" LIKE %(pattern)s;',
                        parameters={'pattern': like_pattern}
                    )
                    for rec in recs:
                        comp_id = rec[0]
                        dash_recs = dashboard_hook.get_records(
                            'SELECT id, "index", name, components, icon, updated_at, created_at '
                            'FROM public.dashboards WHERE %(comp_id)s = ANY(components);',
                            parameters={'comp_id': comp_id}
                        )
                        if dash_recs:
                            for dash in dash_recs:
                                dash_id = dash[0]
                                # 刪除該 dashboard 的群組關聯
                                dashboard_hook.run(
                                    'DELETE FROM public.dashboard_groups WHERE dashboard_id = %(dash_id)s;',
                                    parameters={'dash_id': dash_id}
                                )
                                # 刪除該 dashboard
                                dashboard_hook.run(
                                    'DELETE FROM public.dashboards WHERE id = %(dash_id)s;',
                                    parameters={'dash_id': dash_id}
                                )
                                print(f"Deleted dashboard id={dash_id} for component {comp_id}")
                            # 刪除 component
                            dashboard_hook.run(
                                'DELETE FROM public.components WHERE id = %(id)s;',
                                parameters={'id': comp_id}
                            )
                            print(f"Deleted component id={comp_id}")
                            # 直接刪除未被使用的 component
                            dashboard_hook.run(
                                'DELETE FROM public.components WHERE id = %(id)s;',
                                parameters={'id': comp_id}
                            )
                            print(f"Deleted unused component id={comp_id}")

                    # 2) 再刪除 component_charts 與 query_charts
                    for tbl in ["component_charts", "query_charts"]:
                        try:
                            dashboard_hook.run(
                                f'DELETE FROM public.{tbl} WHERE "index" LIKE %(pattern)s;',
                                parameters={'pattern': like_pattern}
                            )
                        except Exception:
                            pass

                # 刪除所有 dashboard name 含底線（即 _pname 結尾）及其 group 關聯
                try:
                    dashboard_hook.run(
                        'DELETE FROM public.dashboard_groups WHERE dashboard_id IN (SELECT id FROM public.dashboards WHERE name ~ %s);',
                        parameters={"0": r'.*_.*$'}
                    )
                except Exception:
                    pass
                try:
                    dashboard_hook.run(
                        'DELETE FROM public.dashboards WHERE name ~ %s;',
                        parameters={"0": r'.*_.*$'}
                    )
                except Exception:
                    pass
                print("已清除所有 disaster_sus_*_% 相關 dashboard、groups、components、charts")
            except Exception as e:
                print(f"刪除過程中發生錯誤（可忽略）: {e}")
            return

        # 有資料：依照不同 dp name 建立或關聯 dashboards & dashboard_groups
        group_id = 171
        dashboard_ids = []
        status_mapping = {
            "disaster_sus_water": {
                "label": "災害累計停水處理概況",
                "sql": '''select * from (
                        SELECT  
                            district AS x_axis,
                            '已完成戶數' AS y_axis,
                            GREATEST(SUM(suspended_water_supply_count - un_without_water),0) AS data
                        FROM public.eoc_damage_case_tpe
                        WHERE dp_name = '{pname}'
                        GROUP BY district
                        UNION ALL
                        SELECT  
                            district AS x_axis,
                            '處理中戶數' AS y_axis,
                            SUM(un_without_water) AS data
                        FROM public.eoc_damage_case_tpe
                        WHERE dp_name = '{pname}'
                        GROUP BY district
                        ) d
                        ORDER BY ARRAY_POSITION(ARRAY[
                        '北投區', '士林區', '內湖區', '南港區', '松山區',
                        '信義區', '中山區', '大同區', '中正區', '萬華區',
                        '大安區', '文山區'
                        ], x_axis);
                        '''
                                        },
                "disaster_sus_power": {
                    "label": "災害累計停電處理概況",
                    "sql": '''select * from (
                        SELECT  
                            district AS x_axis,
                            '處理中戶數' AS y_axis,
                            SUM(un_power_outage) AS data
                        FROM public.eoc_damage_case_tpe
                        WHERE dp_name = '{pname}'
                        GROUP BY district
                        UNION ALL
                        SELECT  
                            district AS x_axis,
                            '已完成戶數' AS y_axis,
                            GREATEST(SUM(suspended_electricity_supply_count - un_power_outage),0) AS data
                        FROM public.eoc_damage_case_tpe
                        WHERE dp_name = '{pname}'
                        GROUP BY district
                        )d
                        ORDER BY ARRAY_POSITION(ARRAY[
                        '北投區', '士林區', '內湖區', '南港區', '松山區',
                        '信義區', '中山區', '大同區', '中正區', '萬華區',
                        '大安區', '文山區'
                        ], x_axis),2 desc
                    '''
            },
            "disaster_sus_tel":  {"label": "災害累計停話處理概況",
                                    "sql": '''select * from (
                            SELECT  
                            district AS x_axis,
                            '已完成戶數' AS y_axis,
                            GREATEST(SUM(suspended_tel_supply_count - un_tel_temp_discon),0) AS data
                        FROM public.eoc_damage_case_tpe
                        WHERE dp_name = '{pname}'
                        GROUP BY district
                        UNION ALL
                        SELECT  
                            district AS x_axis,
                            '處理中戶數' AS y_axis,
                            SUM(un_tel_temp_discon) AS data
                        FROM public.eoc_damage_case_tpe
                        WHERE dp_name = '{pname}'
                        GROUP BY district
                        ) d
                        ORDER BY ARRAY_POSITION(ARRAY[
                        '北投區', '士林區', '內湖區', '南港區', '松山區',
                        '信義區', '中山區', '大同區', '中正區', '萬華區',
                        '大安區', '文山區'
                        ], x_axis);
                        '''},
            "disaster_sus_gas":   {"label":"災害累計停氣處理概況",
                                    "sql":'''select * from (
                        SELECT  
                            district AS x_axis,
                            '已完成戶數' AS y_axis,
                            GREATEST(SUM(suspended_gas_supply_count - un_gas),0) AS data
                        FROM public.eoc_damage_case_tpe
                        WHERE dp_name = '{pname}'
                        GROUP BY district
                        UNION ALL
                        SELECT  
                            district AS x_axis,
                            '處理中戶數' AS y_axis,
                            SUM(un_gas) AS data
                        FROM public.eoc_damage_case_tpe
                        WHERE dp_name = '{pname}'
                        GROUP BY district
                        )d
                        ORDER BY ARRAY_POSITION(ARRAY[
                        '北投區', '士林區', '內湖區', '南港區', '松山區',
                        '信義區', '中山區', '大同區', '中正區', '萬華區',
                        '大安區', '文山區'
                        ], x_axis);
                        '''}
        }
        for pname in unique_names:
            print(f"處理 pname: {pname}")
            # 若 dashboard 已存在，直接結束排程
            exists = dashboard_hook.get_records(
                'SELECT 1 FROM public.dashboards WHERE name = %(name)s;',
                parameters={'name': pname}
            )
            if exists:
                print(f"dashboard {pname} 已存在，跳出並結束排程")
                continue

            # 建立 component，status_mapping key + _pname 為 component index, status_mapping['label'] + _pname 為 component name
            for status_key, status_val in status_mapping.items():
                comp_index = f"{status_key}_{pname}"
                comp_name = f"{status_val['label']}_{pname}"
                recs = dashboard_hook.get_records(
                    'SELECT id FROM public.components WHERE "index" = %(index)s;',
                    parameters={'index': comp_index}
                )
                if not recs:
                    dashboard_hook.run(
                        'INSERT INTO public.components ("index", name) VALUES (%(index)s, %(name)s);',
                        parameters={'index': comp_index, 'name': comp_name}
                    )
                recs = dashboard_hook.get_records(
                    'SELECT id FROM public.components WHERE "index" = %(index)s;',
                    parameters={'index': comp_index}
                )
                comp_id = recs[0][0]
                print(f"已建立或確認 component id={comp_id}, index={comp_index}, name={comp_name}")

                # Use get_pandas_df to directly get the DataFrame
                df = dashboard_hook.get_pandas_df(
                    sql='SELECT * FROM public.query_charts WHERE "index" = %(status_key)s;',
                    parameters={'status_key': status_key}
                )

                # Check if the DataFrame is not empty
                if not df.empty:
                    # No need to get colnames or create df manually anymore
                    # df = pd.DataFrame([dict(zip(colnames, row)) for row in chart_records]) # Removed

                    # Modify index 與 query_chart 欄位
                    df["index"] = f"{status_key}_{pname}"
                    df["query_chart"] = status_val['sql'].format(pname=pname)

                    # Enhanced cleaning for other JSON-like columns
                    json_like_cols = ['links', 'contributors', 'history_config', 'map_filter']
                    for col in json_like_cols:
                        if col in df.columns:
                            def clean_json_col(val):
                                if isinstance(val, (dict, list)):
                                    return json.dumps(val)
                                elif isinstance(val, str):
                                    val_stripped = val.strip()
                                    if (val_stripped.startswith('[') and val_stripped.endswith(']')) or \
                                       (val_stripped.startswith('{') and val_stripped.endswith('}')):
                                        try:
                                            parsed = json.loads(val_stripped)
                                            return json.dumps(parsed)
                                        except json.JSONDecodeError:
                                            print(f"Warning: Failed to parse column '{col}': {val}")
                                            return None
                                return val
                            df[col] = df[col].apply(clean_json_col)

                    # Upsert back to query_charts
                    pg_engine = create_engine(dashboard_hook.get_uri())
                    with pg_engine.begin() as conn:
                        conn.execute(text('DELETE FROM public.query_charts WHERE "index" = :idx'), {"idx": f"{status_key}_{pname}"})
                        # Convert links and contributors JSON strings to Python lists for Postgres array columns
                        for arr_col in ['links', 'contributors']:
                            if arr_col in df.columns:
                                def to_py_list(val):
                                    if isinstance(val, str):
                                        try:
                                            arr = json.loads(val)
                                            if isinstance(arr, list):
                                                return arr
                                        except json.JSONDecodeError:
                                            pass
                                    return val
                                df[arr_col] = df[arr_col].apply(to_py_list)
                        df.to_sql(
                            'query_charts',
                            conn,
                            if_exists='append',
                            index=False,
                            method='multi'
                        )
                    print(f"已用 DataFrame upsert query_charts index={status_key}_{pname}")
                
                # --- 修改 component_charts ---
                # 使用 get_pandas_df 取得 component_charts 的範本資料
                df_chart_template = dashboard_hook.get_pandas_df(
                    sql='SELECT "index", color, "types", unit FROM public.component_charts WHERE "index" = %(index)s;',
                    parameters={'index': status_key}
                )

                if not df_chart_template.empty:
                    new_chart_index = f"{status_key}_{pname}"
                    # 修改 index
                    df_chart_template["index"] = new_chart_index
                    # 將 types 欄位轉成 Python list (符合 Postgres 陣列)
                    if 'types' in df_chart_template.columns:
                        def to_py_list(val):
                            # Convert numpy arrays to Python lists
                            if isinstance(val, np.ndarray):
                                return val.tolist()
                            # Already a Python list
                            if isinstance(val, list):
                                return val
                            # Parse JSON string into Python list
                            if isinstance(val, str):
                                try:
                                    parsed = json.loads(val)
                                    if isinstance(parsed, list):
                                        return parsed
                                except json.JSONDecodeError:
                                    pass
                            return val
                        df_chart_template['types'] = df_chart_template['types'].apply(to_py_list)

                    # upsert 回資料庫 (先刪後寫入)
                    pg_engine = create_engine(dashboard_hook.get_uri())
                    with pg_engine.begin() as conn:
                        # 先刪除舊的 index
                        conn.execute(text('DELETE FROM public.component_charts WHERE "index" = :idx'), {"idx": new_chart_index})
                        # append 新資料
                        df_chart_template.to_sql('component_charts', conn, if_exists='append', index=False, method='multi')
                    print(f"已用 DataFrame upsert component_charts index={new_chart_index}")
                # --- component_charts 修改結束 ---


            # 取得 dashboard id=16 的範本資料
            dashboard_template = dashboard_hook.get_records(
                'SELECT icon FROM public.dashboards WHERE id = 16;'
            )
            icon_val = dashboard_template[0][0] if dashboard_template else None

            # --- 修改取得 component id 的方式 ---
            # 產生所有需要的 component index
            comp_indices_to_fetch = [f"{status_key}_{pname}" for status_key in status_mapping.keys()]
            
            # 使用 get_pandas_df 一次取得所有 component id
            if comp_indices_to_fetch:
                sql_get_ids = 'SELECT id FROM public.components WHERE "index" = ANY(%(indices)s);'
                df_comp_ids = dashboard_hook.get_pandas_df(sql=sql_get_ids, parameters={'indices': comp_indices_to_fetch})
                comp_ids = df_comp_ids['id'].tolist() if not df_comp_ids.empty else []
            else:
                comp_ids = []

            # 另外查詢 'eoc_disaster_summary' 的 id 並加入 comp_ids
            df_summary_id = dashboard_hook.get_pandas_df(
                sql='SELECT id FROM public.components WHERE "index" = %(index)s;',
                parameters={'index': 'eoc_disaster_summary'}
            )
            if not df_summary_id.empty:
                summary_id = df_summary_id['id'].iloc[0]
                if summary_id not in comp_ids:
                    comp_ids.append(summary_id)

            # --- component id 取得修改結束 ---

            # 刪除舊的同名 dashboard（確保不重複）
            dashboard_hook.run(
                'DELETE FROM public.dashboards WHERE name = %(name)s;',
                parameters={'name': pname}
            )

            # 隨機 12 位 hex 作為 dashboards."index"
            rand_idx = ''.join(random.choices('0123456789abcdef', k=12))

            # 將 comp_ids 轉為 Python int，避免 numpy.int64 導致 psycopg2 can't adapt type
            comp_ids = [int(x) for x in comp_ids]

            # 插入 dashboard 並帶上隨機 index、name=pname、components 會轉成 {x,y,z} 格式
            dashboard_hook.run(
                'INSERT INTO public.dashboards ("index","name",components,icon,created_at,updated_at) '
                'VALUES (%(idx)s,%(name)s,%(components)s,%(icon)s,%(created_at)s,%(updated_at)s);',
                parameters={
                    'idx': rand_idx,
                    'name': pname,
                    'components': comp_ids,
                    'icon': icon_val,
                    'created_at': datetime.now(timezone.utc),
                    'updated_at': datetime.now(timezone.utc)
                }
            )
            print(f"已建立/更新 dashboard: idx={rand_idx}, name={pname}, components={comp_ids}")
            
            # 新建立好的dashboard,取得id,然後配上group_id= 171 寫入dashboard_groups (維持 get_records + run)
            dash_id_records = dashboard_hook.get_records(
                'SELECT id FROM public.dashboards WHERE name = %(name)s;',
                parameters={'name': pname}
            )
            if dash_id_records:
                dashboard_id = dash_id_records[0][0]
                dashboard_hook.run(
                    'INSERT INTO public.dashboard_groups (dashboard_id, group_id) '
                    'VALUES (%(dashboard_id)s, 171) ON CONFLICT DO NOTHING;',
                    parameters={'dashboard_id': dashboard_id}
                )
                print(f"已建立 dashboard_groups 關聯: dashboard_id={dashboard_id}, group_id={group_id}")





    # except Exception as e:
    #     print(f"執行過程中發生錯誤: {e}")
    #     raise

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='eoc_dashboard_controller')
dag.create_dag(etl_func=_transfer)
