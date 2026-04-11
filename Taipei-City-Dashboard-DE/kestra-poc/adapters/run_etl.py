"""Kestra entry point that calls an existing Airflow DAG's `_transfer` function.

Usage (透過 Kestra flow 呼叫):
    python /opt/adapters/run_etl.py <proj_folder> <dag_folder>

參數會對應到 dags/<proj_folder>/<dag_folder>/<dag_folder>.py 裡的 `_transfer`
函式，並從同資料夾的 job_config.json 載入 dag_infos。所有 DB 連線字串透過
環境變數（READY_DATA_DB_URI 等）傳入，PostgresHook 會由 airflow_shim 提供。
"""

import importlib.util
import json
import os
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print("Usage: run_etl.py <proj_folder> <dag_folder>", file=sys.stderr)
        sys.exit(2)

    proj_folder = sys.argv[1]
    dag_folder = sys.argv[2]

    dags_root = Path(os.environ.get("DAG_PATH", "/opt/airflow/dags"))
    if not dags_root.exists():
        raise SystemExit(f"DAG_PATH {dags_root} 不存在，檢查 bind-mount 設定")

    # 1. 讓 `from operators.common_pipeline import ...` 與 `utils.*` 可以被 import
    sys.path.insert(0, str(dags_root))

    # 2. 安裝 airflow shim（必須在 import DAG module 之前）
    import airflow_shim

    airflow_shim.install()

    # 3. 載入該 DAG 的 job_config.json
    dag_path = dags_root / proj_folder / dag_folder
    config_file = dag_path / "job_config.json"
    if not config_file.exists():
        raise SystemExit(f"找不到 {config_file}")
    config = json.loads(config_file.read_text(encoding="utf-8"))
    dag_infos = config["dag_infos"]

    # 4. 用檔案路徑方式 import，避免 package structure 問題
    dag_module_file = dag_path / f"{dag_folder}.py"
    if not dag_module_file.exists():
        raise SystemExit(f"找不到 DAG 檔 {dag_module_file}")

    spec = importlib.util.spec_from_file_location(
        f"etl_{proj_folder}_{dag_folder}", dag_module_file
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # 會執行 DAG 檔最後的 CommonDag(...).create_dag(...)，
    # 因為 shim 的關係所有 Airflow 相關呼叫都會是 no-op

    transfer = getattr(module, "_transfer", None)
    if transfer is None:
        raise SystemExit(
            f"{dag_module_file} 沒有 `_transfer` 函式，無法沿用此 adapter"
        )

    # 5. 組出原本 Airflow op_kwargs 的內容，直接呼叫 _transfer
    kwargs = {
        "dag_infos": dag_infos,
        "ready_data_db_uri": os.environ["READY_DATA_DB_URI"],
        "raw_data_db_uri": os.environ.get("RAW_DATA_DB_URI", os.environ["READY_DATA_DB_URI"]),
        "proxies": None,
        "data_path": os.environ.get("DATA_PATH", "/opt/airflow/data"),
    }
    print(f"[kestra-adapter] invoking _transfer for {proj_folder}/{dag_folder}")
    transfer(**kwargs)
    print(f"[kestra-adapter] done: {proj_folder}/{dag_folder}")


if __name__ == "__main__":
    main()
