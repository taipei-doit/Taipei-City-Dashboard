"""自行車路網每日更新 — 每天 20:00 (Asia/Taipei)

原始 Airflow DAG: proj_city_dashboard.bike_path
目標 Windmill worker group / tag: default

把這個檔案內容貼進 Windmill UI 的新 Python script，並在 script 設定：
  - Tag: default
  - 建立 Schedule: 6-field cron "0 0 20 * * *"  timezone Asia/Taipei
"""

import sys

sys.path.insert(0, "/opt/adapters")


def main():
    from dag_runner import run_dag

    return run_dag("proj_city_dashboard", "bike_path")
