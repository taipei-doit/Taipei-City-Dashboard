"""Reusable helper that invokes an existing Airflow DAG's `_transfer` function.

用法（從 Windmill 的 Python script 呼叫）：

    import sys
    sys.path.insert(0, "/opt/adapters")
    from dag_runner import run_dag

    def main():
        run_dag("proj_city_dashboard", "eoc_dashboard_controller")
"""

import importlib.util
import json
import os
import sys
from pathlib import Path


def run_dag(proj_folder: str, dag_folder: str):
    """Run a legacy Airflow DAG's `_transfer` function with env-based config.

    - 從 `$DAG_PATH/<proj>/<dag>/job_config.json` 讀 dag_infos
    - 安裝 airflow shim（把 airflow.* 換成 no-op / Postgres URI 版）
    - 以檔案路徑方式 import `<dag>.py`，再取出 `_transfer` 呼叫

    DB 連線字串經由環境變數傳入（READY_DATA_DB_URI / RAW_DATA_DB_URI /
    DASHBOARD_DB_URI），正式環境建議改用 Windmill Resource（type: postgresql）
    讀進來後用 `os.environ[...] = ...` 臨時注入即可。
    """
    dags_root = Path(os.environ.get("DAG_PATH", "/opt/airflow/dags"))
    if not dags_root.exists():
        raise RuntimeError(
            f"DAG_PATH {dags_root} 不存在，檢查 worker container 的 bind-mount"
        )

    if str(dags_root) not in sys.path:
        sys.path.insert(0, str(dags_root))

    import airflow_shim

    airflow_shim.install()

    dag_path = dags_root / proj_folder / dag_folder
    config_file = dag_path / "job_config.json"
    if not config_file.exists():
        raise RuntimeError(f"找不到 {config_file}")

    config = json.loads(config_file.read_text(encoding="utf-8"))
    dag_infos = config["dag_infos"]

    dag_module_file = dag_path / f"{dag_folder}.py"
    if not dag_module_file.exists():
        raise RuntimeError(f"找不到 DAG 檔 {dag_module_file}")

    spec = importlib.util.spec_from_file_location(
        f"etl_{proj_folder}_{dag_folder}", dag_module_file
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    # 執行 DAG 檔末尾的 CommonDag(...).create_dag(...)，shim 的關係下全部是 no-op
    spec.loader.exec_module(module)

    transfer = getattr(module, "_transfer", None)
    if transfer is None:
        raise RuntimeError(f"{dag_module_file} 沒有 `_transfer` 函式")

    kwargs = {
        "dag_infos": dag_infos,
        "ready_data_db_uri": os.environ["READY_DATA_DB_URI"],
        "raw_data_db_uri": os.environ.get(
            "RAW_DATA_DB_URI", os.environ["READY_DATA_DB_URI"]
        ),
        "proxies": None,
        "data_path": os.environ.get("DATA_PATH", "/opt/airflow/data"),
    }
    print(f"[windmill-adapter] invoking _transfer for {proj_folder}/{dag_folder}")
    transfer(**kwargs)
    print(f"[windmill-adapter] done: {proj_folder}/{dag_folder}")
    return {"proj": proj_folder, "dag": dag_folder, "status": "ok"}
