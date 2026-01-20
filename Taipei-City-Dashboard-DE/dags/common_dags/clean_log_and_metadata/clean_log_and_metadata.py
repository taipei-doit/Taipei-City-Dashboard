import logging
import os
import subprocess
import re
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


def _get_airflow_db_cleanup_help_text() -> str:
    try:
        res = subprocess.run(
            ["airflow", "db", "cleanup", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        return (res.stdout or "") + "\n" + (res.stderr or "")
    except Exception:
        logging.exception("Failed to run `airflow db cleanup --help`")
        return ""


def _get_airflow_db_help_text() -> str:
    try:
        res = subprocess.run(
            ["airflow", "db", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        return (res.stdout or "") + "\n" + (res.stderr or "")
    except Exception:
        logging.exception("Failed to run `airflow db --help`")
        return ""


def _detect_db_clean_subcommand() -> str:
    """Detect which Airflow db subcommand to use for metadata cleanup.

    Airflow CLI varies by version:
    - Some versions provide `airflow db cleanup`
    - Others provide `airflow db clean`
    """

    help_text = _get_airflow_db_help_text()
    # Prefer `clean` if present, because 2.10+ uses it.
    if re.search(r"\n\s*clean\s+", help_text):
        return "clean"
    if re.search(r"\n\s*cleanup\s+", help_text):
        return "cleanup"

    # Fallback: try to see if cleanup help works.
    cleanup_help = _get_airflow_db_cleanup_help_text()
    if cleanup_help and "invalid choice" not in cleanup_help.lower():
        return "cleanup"

    raise RuntimeError("Could not detect Airflow DB cleanup subcommand (expected `clean` or `cleanup`).")


def _get_airflow_db_clean_help_text(subcommand: str) -> str:
    try:
        res = subprocess.run(
            ["airflow", "db", subcommand, "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        return (res.stdout or "") + "\n" + (res.stderr or "")
    except Exception:
        logging.exception("Failed to run `airflow db %s --help`", subcommand)
        return ""


def _pick_confirmation_flag(help_text: str) -> str | None:
    if "--yes" in help_text:
        return "--yes"
    if re.search(r"\s-y[\s,]", help_text) or re.search(r"\(-y\)", help_text):
        return "-y"
    if "--confirm" in help_text:
        return "--confirm"
    if "--skip-confirmation" in help_text:
        return "--skip-confirmation"
    if "--no-confirm" in help_text:
        return "--no-confirm"
    return None


def _looks_like_cli_parse_error(stderr_text: str) -> bool:
    if not stderr_text:
        return False
    lowered = stderr_text.lower()
    return any(
        token in lowered
        for token in [
            "no such option",
            "unrecognized arguments",
            "unknown option",
            "invalid choice",
            "usage:",
        ]
    )


def _pick_timestamp_flag_candidates(help_text: str) -> list[str]:
    candidates: list[str] = []

    # Prefer explicit flags if shown in help.
    for flag in [
        "--clean-before-timestamp",
        "--clean-before",
        "--clean-before-date",
        "--before-timestamp",
        "--before",
    ]:
        if help_text and flag in help_text:
            candidates.append(flag)

    # Fallback to common/legacy names.
    candidates.extend(
        [
            "--clean-before-timestamp",
            "--clean-before",
            "--before",
        ]
    )

    # De-dup while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for flag in candidates:
        if flag not in seen:
            seen.add(flag)
            ordered.append(flag)
    return ordered


def _run_airflow_db_cleanup(cutoff_timestamp: str) -> dict:
    subcommand = _detect_db_clean_subcommand()
    help_text = _get_airflow_db_clean_help_text(subcommand)
    confirm_flag = _pick_confirmation_flag(help_text)
    supports_skip_archive = "--skip-archive" in help_text

    timestamp_flags = _pick_timestamp_flag_candidates(help_text)
    if help_text and f"db {subcommand}" not in help_text.lower():
        logging.info("`airflow db %s --help` output captured (may be truncated).", subcommand)

    if help_text and "--clean-before-timestamp" not in help_text and "--before" not in help_text:
        logging.warning(
            "`airflow db %s --help` did not list known timestamp flags; will try common variants.",
            subcommand,
        )

    # Try a few combinations to handle Airflow CLI changes.
    confirm_variants: list[tuple[str | None, str | None]] = []
    if confirm_flag:
        confirm_variants.append((confirm_flag, None))
    # Last resort: feed confirmation via stdin.
    confirm_variants.append((None, "y\n"))

    skip_archive_variants = [True, False] if supports_skip_archive else [False]

    last_stdout = ""
    last_stderr = ""
    last_returncode: int | None = None

    for ts_flag in timestamp_flags:
        for use_skip_archive in skip_archive_variants:
            for cf, stdin_text in confirm_variants:
                cmd = ["airflow", "db", subcommand, ts_flag, cutoff_timestamp]
                if use_skip_archive:
                    cmd.append("--skip-archive")
                if cf:
                    cmd.append(cf)

                logging.info("Running: %s", " ".join(cmd))
                res = subprocess.run(
                    cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    input=stdin_text,
                )

                last_stdout = res.stdout or ""
                last_stderr = res.stderr or ""
                last_returncode = res.returncode

                if last_stdout:
                    logging.info("airflow db cleanup stdout:\n%s", last_stdout)
                if last_stderr:
                    logging.warning("airflow db cleanup stderr:\n%s", last_stderr)

                if res.returncode == 0:
                    return {"ok": True, "cmd": cmd, "returncode": res.returncode}

                # If it looks like a CLI parse error, try next variant.
                if res.returncode == 2 or _looks_like_cli_parse_error(last_stderr):
                    logging.warning("DB cleanup command variant not accepted; trying next variant.")
                    continue

                # Non-CLI failure (DB locked, permission, etc.) -> fail fast.
                raise RuntimeError(f"airflow db cleanup failed with exit code {res.returncode}")

    raise RuntimeError(
        f"All airflow db cleanup command variants failed (last exit={last_returncode})."
    )


def _transfer(**kwargs):
    dag_infos = kwargs.get("dag_infos", {})
    retention_days = int(dag_infos.get("retention_days", 7))
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(days=retention_days)
    cutoff_timestamp = cutoff.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

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

    db_cleanup_res = _run_airflow_db_cleanup(cutoff_timestamp)
    logging.info("Airflow DB cleanup done: %s", db_cleanup_res)

    total_deleted_files = sum(r.get("deleted_files", 0) for r in results)
    total_deleted_dirs = sum(r.get("deleted_dirs", 0) for r in results)
    logging.info("Log cleanup summary: deleted_files=%d, deleted_dirs=%d", total_deleted_files, total_deleted_dirs)


dag = CommonDag(proj_folder="common_dags", dag_folder="clean_log_and_metadata")
dag.create_dag(etl_func=_transfer)
