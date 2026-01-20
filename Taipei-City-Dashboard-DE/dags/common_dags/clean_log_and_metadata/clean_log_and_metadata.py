import logging
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from airflow.configuration import conf
from operators.common_pipeline import CommonDag


def _safe_under(base: Path, target: Path) -> bool:
    try:
        base_resolved = base.resolve()
        target_resolved = target.resolve()
        return base_resolved == target_resolved or base_resolved in target_resolved.parents
    except Exception:
        return False


def _delete_old_logs(root: Path, cutoff: datetime) -> dict:
    deleted_files = 0
    deleted_dirs = 0
    scanned_files = 0

    if not root.exists():
        logging.info("Log folder not found, skip: %s", str(root))
        return {
            "root": str(root),
            "scanned_files": 0,
            "deleted_files": 0,
            "deleted_dirs": 0,
            "skipped": True,
        }

    for current_root, dirnames, filenames in os.walk(root, topdown=False):
        current_path = Path(current_root)

        for filename in filenames:
            file_path = current_path / filename
            try:
                scanned_files += 1
                stat = file_path.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    file_path.unlink(missing_ok=True)
                    deleted_files += 1
            except FileNotFoundError:
                continue
            except Exception:
                logging.exception("Failed to process log file: %s", str(file_path))

        for dirname in dirnames:
            dir_path = current_path / dirname
            try:
                if dir_path.exists() and dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    deleted_dirs += 1
            except Exception:
                continue

    return {
        "root": str(root),
        "scanned_files": scanned_files,
        "deleted_files": deleted_files,
        "deleted_dirs": deleted_dirs,
        "skipped": False,
    }


def _run_airflow_db_cleanup(cutoff_date_str: str) -> dict:
    candidates = [
        ["airflow", "db", "cleanup", "--clean-before-timestamp", cutoff_date_str, "--yes"],
        ["airflow", "db", "cleanup", "--clean-before-timestamp", cutoff_date_str, "-y"],
        [
            "airflow",
            "db",
            "cleanup",
            "--clean-before-timestamp",
            cutoff_date_str,
            "--skip-archive",
            "--yes",
        ],
        [
            "airflow",
            "db",
            "cleanup",
            "--clean-before-timestamp",
            cutoff_date_str,
            "--skip-archive",
            "-y",
        ],
    ]

    last_error = None
    for cmd in candidates:
        try:
            logging.info("Running: %s", " ".join(cmd))
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return {"ok": True, "cmd": cmd}
        except Exception as exc:
            last_error = exc
            logging.warning("DB cleanup command failed, will try next candidate.")

    raise RuntimeError("All airflow db cleanup command variants failed") from last_error


def _transfer(**kwargs):
    dag_infos = kwargs.get("dag_infos", {})
    retention_days = int(dag_infos.get("retention_days", 7))
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(days=retention_days)
    cutoff_date_str = cutoff.strftime("%Y-%m-%d")

    base_log_folder = Path(
        conf.get("logging", "base_log_folder", fallback=os.path.join(os.getenv("AIRFLOW_HOME", "/opt/airflow"), "logs"))
    )
    base_log_folder = base_log_folder.expanduser()

    if not _safe_under(Path("/"), base_log_folder):
        raise RuntimeError(f"Unsafe base_log_folder resolved to: {base_log_folder}")

    protected = {"scheduler", "webserver", "triggerer", "dag_processor_manager"}
    scheduler_root = base_log_folder / "scheduler"
    dag_log_roots = []
    if base_log_folder.exists():
        for child in base_log_folder.iterdir():
            if not child.is_dir():
                continue
            if child.name in protected:
                continue
            dag_log_roots.append(child)

    logging.info("Retention days=%d, cutoff=%s", retention_days, cutoff.isoformat())
    logging.info("Base log folder: %s", str(base_log_folder))

    results = []
    results.append(_delete_old_logs(scheduler_root, cutoff))
    for root in dag_log_roots:
        results.append(_delete_old_logs(root, cutoff))

    db_cleanup_res = _run_airflow_db_cleanup(cutoff_date_str)
    logging.info("Airflow DB cleanup done: %s", db_cleanup_res)

    total_deleted_files = sum(r.get("deleted_files", 0) for r in results)
    total_deleted_dirs = sum(r.get("deleted_dirs", 0) for r in results)
    logging.info("Log cleanup summary: deleted_files=%d, deleted_dirs=%d", total_deleted_files, total_deleted_dirs)


dag = CommonDag(proj_folder="common_dags", dag_folder="clean_log_and_metadata")
dag.create_dag(etl_func=_transfer)
