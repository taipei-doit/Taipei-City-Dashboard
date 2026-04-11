"""EOC 儀表板控制器 — 每 5 分鐘執行

原始 Airflow DAG: proj_city_dashboard.eoc_dashboard_controller
目標 Windmill worker group / tag: realtime

把這個檔案內容貼進 Windmill UI 的新 Python script，並在 script 設定：
  - Tag: realtime
  - 建立 Schedule: 6-field cron "0 */5 * * * *"  timezone Asia/Taipei
"""

import sys

sys.path.insert(0, "/opt/adapters")


def main():
    from dag_runner import run_dag

    return run_dag("proj_city_dashboard", "eoc_dashboard_controller")
