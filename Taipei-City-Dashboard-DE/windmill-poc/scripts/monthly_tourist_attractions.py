"""臺北旅遊網景點資料 — 每月 1 號 00:00 (Asia/Taipei)

原始 Airflow DAG: proj_city_dashboard.tourist_attractions
目標 Windmill worker group / tag: heavy

把這個檔案內容貼進 Windmill UI 的新 Python script，並在 script 設定：
  - Tag: heavy
  - 建立 Schedule: 6-field cron "0 0 0 1 * *"  timezone Asia/Taipei
"""

import sys

sys.path.insert(0, "/opt/adapters")


def main():
    from dag_runner import run_dag

    return run_dag("proj_city_dashboard", "tourist_attractions")
