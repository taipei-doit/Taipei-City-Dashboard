#!/usr/bin/env python3
"""scan_all_tests.py — 一次跑完所有 DAG 的 source URL 測試,匯總結果。

維護者用,讓你不必逐個進每個 DAG 資料夾跑 test。

預設會掃 `Taipei-City-Dashboard-DE/dags/` 下全部 `test_*.py`(不含 utils/operators 等非 DAG 目錄,但會掃到所有 DAG 子目錄)。

Run:
    python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py

只跑某個 proj 或某個 team 提交的 DAG:
    python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py \\
        Taipei-City-Dashboard-DE/dags/proj_city_dashboard

只跑單一 DAG:
    python Taipei-City-Dashboard-DE/dag-toolkit/scripts/scan_all_tests.py \\
        Taipei-City-Dashboard-DE/dags/proj_city_dashboard/<table_name>

退出碼:
    0 — 全部通過
    1 — 有 FAIL
    2 — 路徑錯 / 沒找到 test
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


DEFAULT_ROOT = Path("Taipei-City-Dashboard-DE/dags")
TIMEOUT_SECONDS = 120
EXCLUDE_DIR_NAMES = {
    "__pycache__",
    "utils",
    "operators",
    "settings",
    "tutorial",
    "preprocess",
    "opendata",
    "tests",
    "reports",
}


def find_test_files(root: Path) -> list[Path]:
    tests: list[Path] = []
    for path in root.rglob("test_*.py"):
        # 排除快取與非 DAG 目錄
        if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
            continue
        # DAG 資料夾的 test 一定與 job_config.json 同層
        if not (path.parent / "job_config.json").exists():
            continue
        tests.append(path)
    return sorted(tests)


def run_test(test_file: Path) -> tuple[bool, str, float]:
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, test_file.name],
            cwd=str(test_file.parent),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        elapsed = time.time() - start
        output = (proc.stdout + proc.stderr).strip()
        return proc.returncode == 0, output, elapsed
    except subprocess.TimeoutExpired:
        return False, f"TIMEOUT (>{TIMEOUT_SECONDS}s)", TIMEOUT_SECONDS
    except Exception as e:
        return False, f"RUN ERROR: {type(e).__name__}: {e}", time.time() - start


def _short_summary_line(test_file: Path, root: Path) -> str:
    try:
        rel = test_file.relative_to(root)
    except ValueError:
        rel = test_file
    return str(rel)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "target",
        nargs="?",
        default=str(DEFAULT_ROOT),
        help=f"要掃的目錄(預設 {DEFAULT_ROOT})",
    )
    parser.add_argument("--no-color", action="store_true", help="不要輸出顏色")
    parser.add_argument("-v", "--verbose", action="store_true", help="即使 PASS 也印詳細輸出")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"❌ 路徑不存在: {target}", file=sys.stderr)
        return 2

    # 顏色控制
    if args.no_color or not sys.stdout.isatty():
        green = red = yellow = bold = reset = ""
    else:
        green, red, yellow, bold, reset = "\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[0m"

    # 若 target 本身是 DAG 資料夾(有 job_config.json),只跑該支
    if (target / "job_config.json").exists():
        candidates = list(target.glob("test_*.py"))
        if not candidates:
            print(f"❌ DAG 資料夾沒有 test_*.py: {target}", file=sys.stderr)
            return 2
        tests = candidates
        scan_root = target.parent
    else:
        tests = find_test_files(target)
        scan_root = target

    if not tests:
        print(f"⚠️  沒找到 test_*.py(同層需有 job_config.json): {target}")
        return 2

    print(f"{bold}掃描 {scan_root}{reset}")
    print(f"找到 {len(tests)} 支測試\n")

    results: list[tuple[Path, bool, str, float]] = []
    for tf in tests:
        rel = _short_summary_line(tf, scan_root)
        print(f"  RUN  {rel} ... ", end="", flush=True)
        ok, output, elapsed = run_test(tf)
        marker = f"{green}✅ PASS{reset}" if ok else f"{red}❌ FAIL{reset}"
        print(f"{marker}  ({elapsed:.1f}s)")
        if args.verbose and ok and output:
            for line in output.splitlines():
                print(f"       {line}")
        results.append((tf, ok, output, elapsed))

    passed = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    print()
    print("=" * 60)
    print(f"{bold}總結{reset}: {green}PASS {len(passed)}{reset} / {red}FAIL {len(failed)}{reset} / 總 {len(results)}")

    if failed:
        print(f"\n{bold}=== 失敗詳情 ==={reset}")
        for tf, _, output, _ in failed:
            rel = _short_summary_line(tf, scan_root)
            print(f"\n{red}--- {rel} ---{reset}")
            tail = output.splitlines()[-20:] if output else ["(no output)"]
            for line in tail:
                print(f"  {line}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
