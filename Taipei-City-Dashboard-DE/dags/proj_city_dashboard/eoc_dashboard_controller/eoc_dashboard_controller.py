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
            dashboard_hook = PostgresHook(postgres_conn_id="dashboad-postgre")

            # 無資料：刪除關聯並結束
            if not unique_names:
                # 查詢所有 disaster_sus_*_% 結尾的 component，並刪除相關 dashboard、groups、components、charts
                dashboard_hook = PostgresHook(postgres_conn_id="dashboad-postgre")
                status_keys = ["disaster_sus_water", "disaster_sus_power", "disaster_sus_tel", "disaster_sus_gas"]
                # 1. 刪除所有 disaster_sus_*_% 的 component_charts, query_charts, components
                for status_key in status_keys:
                    like_pattern = f"{status_key}_%"
                    dashboard_hook.run('DELETE FROM public.component_charts WHERE "index" LIKE %(like)s;', parameters={'like': like_pattern})
                    dashboard_hook.run('DELETE FROM public.query_charts WHERE "index" LIKE %(like)s;', parameters={'like': like_pattern})
                    dashboard_hook.run('DELETE FROM public.components WHERE "index" LIKE %(like)s;', parameters={'like': like_pattern})
                # 2. 刪除所有 dashboard name 結尾為 _pname 的 dashboard 及其 group 關聯
                dashboard_hook.run(
                    'DELETE FROM public.dashboard_groups WHERE dashboard_id IN (SELECT id FROM public.dashboards WHERE name ~ %s);',
                    parameters={"0": r'.*_.*$'}
                )
                dashboard_hook.run(
                    'DELETE FROM public.dashboards WHERE name ~ %s;',
                    parameters={"0": r'.*_.*$'}
                )
                print("已清除所有 disaster_sus_*_% 相關 dashboard、groups、components、charts")
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
                    dashboard_hook.run(
                        "INSERT INTO public.components (\"index\", name) "
                        "VALUES (%(index)s, %(name)s) ON CONFLICT (\"index\") DO NOTHING;",
                        parameters={'index': comp_index, 'name': comp_name}
                    )
                    recs = dashboard_hook.get_records(
                        "SELECT id FROM public.components WHERE \"index\" = %(index)s;",
                        parameters={'index': comp_index}
                    )
                    comp_id = recs[0][0]
                    print(f"已建立或確認 component id={comp_id}, index={comp_index}, name={comp_name}")

                    chart_records = dashboard_hook.get_records(
                        '''SELECT * FROM public.query_charts WHERE "index" = %(status_key)s;''',
                        parameters={'status_key': status_key}
                    )
                    if chart_records:
                        (orig_idx, history_config, map_config_ids, map_filter,
                         time_from, time_to, update_freq, update_freq_unit, source,
                         short_desc, long_desc, use_case, links, contributors,
                         created_at_orig, updated_at_orig, query_type, _query_chart_tpl,
                         query_history, city_val) = chart_records[0]
                        # 統一使用 status_mapping 的 sql 作為 query_chart，並帶入 pname
                        new_query_chart = status_val['sql'].format(pname=pname)
                        now_ts = datetime.now(timezone.utc)
                        # 插入或更新 query_charts
                        dashboard_hook.run(
                            '''INSERT INTO public.query_charts
                               ("index", history_config, map_config_ids, map_filter, time_from,
                                time_to, update_freq, update_freq_unit, "source", short_desc,
                                long_desc, use_case, links, contributors, created_at,
                                updated_at, query_type, query_chart, query_history, city)
                                VALUES
                               (%(index)s, %(history_config)s, %(map_config_ids)s, %(map_filter)s,
                                %(time_from)s, %(time_to)s, %(update_freq)s, %(update_freq_unit)s,
                                %(source)s, %(short_desc)s, %(long_desc)s, %(use_case)s,
                                %(links)s, %(contributors)s, %(created_at)s,
                                %(updated_at)s, %(query_type)s, %(query_chart)s,
                                %(query_history)s, %(city)s)
                              ON CONFLICT ("index")
                              DO UPDATE SET query_chart = EXCLUDED.query_chart,
                                            updated_at = EXCLUDED.updated_at;''',
                            parameters={
                                'index': comp_index,
                                'history_config': history_config,
                                'map_config_ids': map_config_ids,
                                'map_filter': map_filter,
                                'time_from': time_from,
                                'time_to': time_to,
                                'update_freq': update_freq,
                                'update_freq_unit': update_freq_unit,
                                'source': source,
                                'short_desc': short_desc,
                                'long_desc': long_desc,
                                'use_case': use_case,
                                'links': links,
                                'contributors': contributors,
                                'created_at': created_at_orig,
                                'updated_at': now_ts,
                                'query_type': query_type,
                                'query_chart': new_query_chart,
                                'query_history': query_history,
                                'city': city_val
                            }
                        )
                        print(f"已插入或更新 query_charts index={comp_index}")
                    # 依照 status_mapping 的key 取得 component_charts 的資料後, 寫入一筆新的資料, 僅需修改"index"為 status_key_{pname}
                    chart_template = dashboard_hook.get_records(
                        'SELECT color, "types", unit FROM public.component_charts WHERE "index" = %(index)s;',
                        parameters={'index': status_key}
                    )
                    if chart_template:
                        color, types, unit = chart_template[0]
                        new_chart_index = f"{status_key}_{pname}"
                        dashboard_hook.run(
                            'INSERT INTO public.component_charts ("index", color, "types", unit) '
                            'VALUES (%(index)s, %(color)s, %(types)s, %(unit)s) '
                            'ON CONFLICT ("index") DO NOTHING;',
                            parameters={
                                'index': new_chart_index,
                                'color': color,
                                'types': types,
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





    except Exception as e:
        print(f"執行過程中發生錯誤: {e}")
        raise

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='eoc_dashboard_controller')
dag.create_dag(etl_func=_transfer)
