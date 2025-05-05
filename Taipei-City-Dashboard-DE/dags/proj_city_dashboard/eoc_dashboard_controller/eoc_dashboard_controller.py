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
                # 刪除所有 disaster_sus_*_% 結尾的 component、query_charts、component_charts、dashboard、dashboard_groups
                dashboard_hook = PostgresHook(postgres_conn_id="dashboad-postgre")
                status_keys = ["disaster_sus_water", "disaster_sus_power", "disaster_sus_tel", "disaster_sus_gas"]
                for status_key in status_keys:
                    like_pattern = f"{status_key}_%"
                    try:
                        dashboard_hook.run('DELETE FROM public.component_charts WHERE "index" LIKE %(like)s;', parameters={'like': like_pattern})
                    except Exception:
                        pass
                    try:
                        dashboard_hook.run('DELETE FROM public.query_charts WHERE "index" LIKE %(like)s;', parameters={'like': like_pattern})
                    except Exception:
                        pass
                    try:
                        dashboard_hook.run('DELETE FROM public.components WHERE "index" LIKE %(like)s;', parameters={'like': like_pattern})
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
                    # 將所有 dict 或 list 欄位轉成 json 字串
                    for col in df.columns:
                        if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                            df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
                    # upsert 回資料庫
                    pg_engine = create_engine(dashboard_hook.get_uri())
                    # 先刪除舊的 index
                    with pg_engine.begin() as conn:
                        conn.execute(text('DELETE FROM public.query_charts WHERE "index" = :idx'), {"idx": f"{status_key}_{pname}"})
                    # append 新資料
                    df.to_sql('query_charts', pg_engine, if_exists='append', index=False, method='multi')
                    print(f"已用 DataFrame upsert query_charts index={status_key}_{pname}")
                # 依照 status_mapping 的key 取得 component_charts 的資料後, 寫入一筆新的資料, 僅需修改"index"為 status_key_{pname}
                chart_template = dashboard_hook.get_records(
                    'SELECT color, "types", unit FROM public.component_charts WHERE "index" = %(index)s;',
                    parameters={'index': status_key}
                )
                if chart_template:
                    color, types, unit = chart_template[0]
                    new_chart_index = f"{status_key}_{pname}"
                    # Convert types to JSON string if it's a list or dict
                    if isinstance(types, (dict, list)):
                        types_param = json.dumps(types)
                    else:
                        types_param = types # Keep original if not list/dict

                    dashboard_hook.run(
                        'INSERT INTO public.component_charts ("index", color, "types", unit) '
                        'VALUES (%(index)s, %(color)s, %(types)s, %(unit)s) '
                        'ON CONFLICT ("index") DO NOTHING;',
                        parameters={
                            'index': new_chart_index,
                            'color': color,
                            'types': types_param, # Use the potentially converted value
                            'unit': unit
                        }
                    )
                    print(f"已建立/確認 component_charts: {new_chart_index}")

            # 取得 dashboard id=16 的範本資料
            dashboard_template = dashboard_hook.get_records(
                'SELECT icon FROM public.dashboards WHERE id = 16;'
            )
            icon_val = dashboard_template[0][0] if dashboard_template else None
            # 取得本次所有 component id
            comp_ids = []
            for status_key in status_mapping.keys():
                comp_index = f"{status_key}_{pname}"
                recs = dashboard_hook.get_records(
                    'SELECT id FROM public.components WHERE "index" = %(index)s;',
                    parameters={'index': comp_index}
                )
                if recs:
                    comp_ids.append(recs[0][0])
            # 建立 dashboard
            dashboard_hook.run(
                'INSERT INTO public.dashboards ("name", components, icon, created_at, updated_at) '
                'VALUES (%(name)s, %(components)s, %(icon)s, %(created_at)s, %(updated_at)s) '
                'ON CONFLICT ("name") DO UPDATE SET components = EXCLUDED.components, updated_at = EXCLUDED.updated_at;',
                parameters={
                    'name': pname,
                    'components': json.dumps(comp_ids),
                    'icon': icon_val,
                    'created_at': datetime.now(timezone.utc),
                    'updated_at': datetime.now(timezone.utc)
                }
            )
            print(f"已建立/更新 dashboard: {pname}, components: {comp_ids}")
            # 新建立好的dashboard,取得id,然後配上group_id= 171 寫入dashboard_groups
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
