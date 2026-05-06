#!/usr/bin/env python3
"""
validate_dag.py — 純 Python 驗證 generate-dag toolkit 產出的 DAG 是否符合規範。

使用方式:
    python validate_dag.py <dag_directory>

例如:
    python validate_dag.py Taipei-City-Dashboard-DE/dags/proj_city_dashboard/some_table

驗證項目:
    [檔案] __init__.py 為空檔
    [檔案] <dir_name>.py 存在
    [檔案] job_config.json 存在且為合法 JSON
    [命名] dag_folder == dag_id == ready_data_default_table
    [config] _validate_config 必填鍵齊全
    [config] default_args.email = ["DEFAULT_EMAIL_LIST"]
    [config] tags 至少 3 項
    [config] schedule_interval 合法
    [config] start_date 合法 YYYY-MM-DD
    [config] history_table 配對
    [.py] 頂層 import 純淨
    [.py] _ensure_ready_table 已定義且被呼叫
    [.py] update_lasttime_in_data_to_dataset_info 已呼叫
    [.py] CommonDag(proj_folder=..., dag_folder=...) 名稱與資料夾一致
    [.py] COL_MAP 解析成功
    [.py] COL_MAP 含 data_time
    [跨檔] is_geometry ↔ wkb_geometry ↔ output_coordinate ↔ gis_format 一致
    [跨檔] 含 geometry → 走 save_geodataframe_to_postgresql;反之走 save_dataframe_to_postgresql

退出碼:
    0 — 全數通過
    1 — 有 FAIL 項目
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


REQUIRED_DAG_INFOS = [
    "dag_id",
    "start_date",
    "schedule_interval",
    "catchup",
    "tags",
    "default_args",
    "ready_data_db",
    "ready_data_default_table",
    "load_behavior",
    "description",
]

ALLOWED_TOP_LEVEL_IMPORTS = {
    ("airflow", "DAG"),
    ("operators.common_pipeline", "CommonDag"),
}

ALLOWED_LOAD_BEHAVIORS = {"append", "replace", "current+history"}

CITY_TAGS = {"Taipei-City", "New-Taipei-City"}

VALID_PROJ_FOLDERS = {"proj_city_dashboard", "proj_new_taipei_city_dashboard"}

CRON_AT_KEYWORDS = {
    "@hourly",
    "@daily",
    "@weekly",
    "@monthly",
    "@quarterly",
    "@yearly",
    "@annually",
    "@once",
}


@dataclass
class Report:
    passes: list[str] = field(default_factory=list)
    fails: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def ok(self, msg: str) -> None:
        self.passes.append(msg)

    def fail(self, msg: str) -> None:
        self.fails.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def render(self) -> str:
        lines = []
        for p in self.passes:
            lines.append(f"  [PASS] {p}")
        for w in self.warnings:
            lines.append(f"  [WARN] {w}")
        for f in self.fails:
            lines.append(f"  [FAIL] {f}")
        lines.append("")
        if self.fails:
            lines.append(
                f"Result: FAIL ({len(self.fails)} fail, {len(self.warnings)} warn, {len(self.passes)} pass)"
            )
        else:
            lines.append(
                f"Result: PASS ({len(self.warnings)} warn, {len(self.passes)} pass)"
            )
        return "\n".join(lines)


def _is_valid_cron(expr: str) -> bool:
    if not isinstance(expr, str):
        return False
    expr = expr.strip()
    if expr in CRON_AT_KEYWORDS:
        return True
    if expr.startswith("@"):
        return False
    parts = expr.split()
    if len(parts) != 5:
        return False
    pattern = re.compile(r"^[\d\*\,\-\/]+$")
    return all(pattern.match(p) for p in parts)


def _check_files_exist(dag_dir: Path, table_name: str, report: Report) -> dict[str, Path] | None:
    init_file = dag_dir / "__init__.py"
    py_file = dag_dir / f"{table_name}.py"
    config_file = dag_dir / "job_config.json"
    test_file = dag_dir / f"test_{table_name}.py"

    missing = []
    if not init_file.exists():
        missing.append(str(init_file))
    if not py_file.exists():
        missing.append(str(py_file))
    if not config_file.exists():
        missing.append(str(config_file))
    if not test_file.exists():
        missing.append(str(test_file))
    if missing:
        for m in missing:
            report.fail(f"檔案不存在: {m}")
        return None

    if init_file.stat().st_size != 0:
        report.fail(f"__init__.py 必須為空檔(目前 {init_file.stat().st_size} bytes)")
    else:
        report.ok("__init__.py 為空檔")

    return {"init": init_file, "py": py_file, "config": config_file, "test": test_file}


def _check_config(config_file: Path, table_name: str, report: Report) -> dict | None:
    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        report.fail(f"job_config.json 不是合法 JSON: {e}")
        return None
    report.ok("job_config.json 為合法 JSON")

    dag_infos = config.get("dag_infos") or {}
    data_infos = config.get("data_infos") or {}

    if not dag_infos:
        report.fail("job_config.json 缺 dag_infos")
        return None

    # 必填鍵
    for key in REQUIRED_DAG_INFOS:
        if key not in dag_infos:
            report.fail(f"dag_infos 缺必填鍵: {key}")
    if all(k in dag_infos for k in REQUIRED_DAG_INFOS):
        report.ok(f"dag_infos 必填鍵齊全({len(REQUIRED_DAG_INFOS)} 項)")

    # 三名一致
    dag_id = dag_infos.get("dag_id")
    table = dag_infos.get("ready_data_default_table")
    if dag_id != table_name:
        report.fail(f"dag_id ({dag_id!r}) 與資料夾名 ({table_name!r}) 不一致")
    if table != table_name:
        report.fail(
            f"ready_data_default_table ({table!r}) 與資料夾名 ({table_name!r}) 不一致"
        )
    if dag_id == table_name and table == table_name:
        report.ok(f"三名一致: dag_folder == dag_id == table_name == {table_name!r}")

    # email
    email = (dag_infos.get("default_args") or {}).get("email")
    if email != ["DEFAULT_EMAIL_LIST"] and not (
        isinstance(email, list)
        and all(isinstance(e, str) and e.endswith("MAIL_LIST") for e in email)
    ):
        report.fail(
            f"default_args.email 必須為 [\"DEFAULT_EMAIL_LIST\"] 或結尾 MAIL_LIST 的 Variable key,目前: {email!r}"
        )
    else:
        report.ok("default_args.email 走 Airflow Variable")

    # tags
    tags = dag_infos.get("tags") or []
    if not isinstance(tags, list) or len(tags) < 3:
        report.fail(f"tags 必須至少 3 項(主分類 + source_dept + city tag),目前: {tags!r}")
    elif not (set(tags) & CITY_TAGS):
        report.fail(f"tags 必須含 'Taipei-City' 或 'New-Taipei-City',目前: {tags!r}")
    else:
        report.ok(f"tags 完整({len(tags)} 項,含 city tag)")

    # schedule
    sched = dag_infos.get("schedule_interval")
    if not _is_valid_cron(sched):
        report.fail(f"schedule_interval 不合法: {sched!r}")
    else:
        report.ok(f"schedule_interval 合法: {sched!r}")

    # start_date
    sd = dag_infos.get("start_date")
    try:
        datetime.strptime(sd, "%Y-%m-%d")
        report.ok(f"start_date 合法: {sd}")
    except (TypeError, ValueError):
        report.fail(f"start_date 不合法 (需 YYYY-MM-DD): {sd!r}")

    # load_behavior
    lb = dag_infos.get("load_behavior")
    if lb not in ALLOWED_LOAD_BEHAVIORS:
        report.fail(f"load_behavior 必須為 {sorted(ALLOWED_LOAD_BEHAVIORS)} 之一,目前: {lb!r}")
    else:
        report.ok(f"load_behavior: {lb}")

    # history_table 配對
    history = dag_infos.get("ready_data_history_table", "")
    if lb == "current+history":
        expected = f"{table_name}_history"
        if history != expected:
            report.fail(
                f"current+history 模式需 ready_data_history_table='{expected}',目前: {history!r}"
            )
        else:
            report.ok(f"history_table 配對正確: {history}")
    else:
        if history not in ("", None):
            report.fail(
                f"非 current+history 模式時 ready_data_history_table 必須為空字串,目前: {history!r}"
            )
        else:
            report.ok("history_table 為空(append/replace 模式)")

    # is_geometry / output_coordinate / gis_format 三者一致
    is_geom = data_infos.get("is_geometry")
    coord = data_infos.get("output_coordinate")
    gis_fmt = data_infos.get("gis_format")

    if is_geom == 1:
        if coord != "EPSG:4326":
            report.fail(f"is_geometry=1 時 output_coordinate 必須為 'EPSG:4326',目前: {coord!r}")
        if not gis_fmt:
            report.fail(f"is_geometry=1 時 gis_format 必填,目前: {gis_fmt!r}")
        if coord == "EPSG:4326" and gis_fmt:
            report.ok(f"geometry 設定一致: gis_format={gis_fmt}, EPSG:4326")
    elif is_geom == 0:
        if gis_fmt:
            report.fail(f"is_geometry=0 時 gis_format 必須為 null,目前: {gis_fmt!r}")
        else:
            report.ok("非 geometry 設定一致")
    else:
        report.fail(f"data_infos.is_geometry 必須為 0 或 1,目前: {is_geom!r}")

    # component_name 必填,snake_case
    component_name = data_infos.get("component_name")
    if not component_name or not isinstance(component_name, str) or not component_name.strip():
        report.fail(
            "data_infos.component_name 必填:此 DAG 餵給哪個前端 component(snake_case 英文)。多 DAG 可共用同一 component name。"
        )
    elif not re.match(r"^[a-z][a-z0-9_]*$", component_name):
        report.fail(
            f"data_infos.component_name='{component_name}' 不符合 snake_case 規則(僅 lowercase + digits + underscore,且首字非數字)"
        )
    else:
        report.ok(f"component_name: {component_name}")

    return config


def _check_py(py_file: Path, table_name: str, proj_folder_expected: str | None, config: dict, report: Report) -> dict:
    """回傳 {"is_geometry_in_py": bool, "col_map": dict, "select_columns": list}"""
    src = py_file.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        report.fail(f"{py_file.name} 語法錯誤: {e}")
        return {}

    # 頂層 import 純淨
    top_level_imports: set[tuple[str, str]] = set()
    bad_top_level: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                bad_top_level.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                top_level_imports.add((mod, alias.name))
                if (mod, alias.name) not in ALLOWED_TOP_LEVEL_IMPORTS:
                    bad_top_level.append(f"from {mod} import {alias.name}")
    if bad_top_level:
        for b in bad_top_level:
            report.fail(f"頂層 import 不純淨: {b}(必須移到函式內)")
    else:
        if ALLOWED_TOP_LEVEL_IMPORTS.issubset(top_level_imports):
            report.ok("頂層 import 純淨(只有 airflow.DAG + CommonDag)")
        else:
            report.fail(
                "頂層必須 import: from airflow import DAG; from operators.common_pipeline import CommonDag"
            )

    # 找 _ensure_ready_table 函式定義
    fn_names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    if "_ensure_ready_table" not in fn_names:
        report.fail("缺函式定義 _ensure_ready_table(請從 toolkit 樣板複製)")
    else:
        report.ok("已定義 _ensure_ready_table")

    # 找 ETL 函式 _<table_name>
    etl_fn_name = f"_{table_name}"
    etl_fn = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == etl_fn_name),
        None,
    )
    if etl_fn is None:
        report.fail(f"缺 ETL 函式定義: {etl_fn_name}(命名規則: _<table_name>)")
        return {}
    report.ok(f"ETL 函式名稱正確: {etl_fn_name}")

    # 找 dag = CommonDag(proj_folder=..., dag_folder=...)
    common_dag_call = None
    for n in ast.walk(tree):
        if (
            isinstance(n, ast.Assign)
            and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Name)
            and n.value.func.id == "CommonDag"
        ):
            common_dag_call = n.value
            break
    if common_dag_call is None:
        report.fail("找不到 dag = CommonDag(...) 呼叫")
    else:
        kwargs = {kw.arg: kw.value for kw in common_dag_call.keywords}
        proj = (
            kwargs["proj_folder"].value
            if "proj_folder" in kwargs and isinstance(kwargs["proj_folder"], ast.Constant)
            else None
        )
        df = (
            kwargs["dag_folder"].value
            if "dag_folder" in kwargs and isinstance(kwargs["dag_folder"], ast.Constant)
            else None
        )
        if df != table_name:
            report.fail(f"CommonDag(dag_folder={df!r}) 與資料夾名 {table_name!r} 不一致")
        else:
            report.ok(f"CommonDag(dag_folder={df!r}) 與資料夾名一致")
        if proj_folder_expected in VALID_PROJ_FOLDERS:
            if proj != proj_folder_expected:
                report.fail(
                    f"CommonDag(proj_folder={proj!r}) 與目錄路徑 {proj_folder_expected!r} 不一致"
                )
            else:
                report.ok(f"CommonDag(proj_folder={proj!r}) 與目錄路徑一致")
        else:
            report.warn(
                f"父目錄 {proj_folder_expected!r} 非 {sorted(VALID_PROJ_FOLDERS)} 之一,跳過 proj_folder 路徑檢查(若這是實際 DAG 而非 example,請放對位置)"
            )
            if proj not in VALID_PROJ_FOLDERS:
                report.fail(
                    f"CommonDag(proj_folder={proj!r}) 必須為 {sorted(VALID_PROJ_FOLDERS)} 之一"
                )

    # 在 ETL 函式內掃 call
    calls_in_etl: list[str] = []
    for n in ast.walk(etl_fn):
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name):
                calls_in_etl.append(n.func.id)
            elif isinstance(n.func, ast.Attribute):
                calls_in_etl.append(n.func.attr)

    if "_ensure_ready_table" not in calls_in_etl:
        report.fail("ETL 函式內未呼叫 _ensure_ready_table")
    else:
        report.ok("ETL 內已呼叫 _ensure_ready_table")

    if "update_lasttime_in_data_to_dataset_info" not in calls_in_etl:
        report.fail("ETL 函式內未呼叫 update_lasttime_in_data_to_dataset_info")
    else:
        report.ok("ETL 內已呼叫 update_lasttime_in_data_to_dataset_info")

    used_geo_save = "save_geodataframe_to_postgresql" in calls_in_etl
    used_df_save = "save_dataframe_to_postgresql" in calls_in_etl
    if not (used_geo_save or used_df_save):
        report.fail("ETL 未呼叫 save_dataframe_to_postgresql 或 save_geodataframe_to_postgresql")
    if used_geo_save and used_df_save:
        report.fail("不可同時呼叫 save_dataframe_to_postgresql 與 save_geodataframe_to_postgresql")

    # 解析 COL_MAP
    col_map: dict[str, str] = {}
    for n in ast.walk(etl_fn):
        if (
            isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id == "COL_MAP"
            and isinstance(n.value, ast.Dict)
        ):
            for k, v in zip(n.value.keys, n.value.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                    col_map[str(k.value)] = str(v.value)
            break
    if not col_map:
        report.fail("ETL 函式內找不到 COL_MAP = {...}(必須是 ETL 函式內 dict literal)")
    else:
        report.ok(f"COL_MAP 解析成功({len(col_map)} 欄)")

    if col_map and "data_time" not in col_map:
        report.fail("COL_MAP 必須含 data_time 欄")
    elif "data_time" in col_map:
        report.ok("COL_MAP 含 data_time")

    # geometry 一致性
    has_wkb_in_col_map = "wkb_geometry" in col_map
    is_geom_config = config.get("data_infos", {}).get("is_geometry") == 1

    if has_wkb_in_col_map and not is_geom_config:
        report.fail(
            "COL_MAP 含 wkb_geometry,但 job_config.data_infos.is_geometry != 1"
        )
    if (not has_wkb_in_col_map) and is_geom_config:
        report.fail(
            "job_config.data_infos.is_geometry == 1,但 COL_MAP 不含 wkb_geometry"
        )
    if has_wkb_in_col_map and not used_geo_save:
        report.fail(
            "COL_MAP 含 wkb_geometry,必須用 save_geodataframe_to_postgresql"
        )
    if (not has_wkb_in_col_map) and used_geo_save:
        report.fail(
            "COL_MAP 不含 wkb_geometry,不應用 save_geodataframe_to_postgresql"
        )
    if has_wkb_in_col_map and is_geom_config and used_geo_save:
        report.ok("geometry 全鏈路一致(COL_MAP / config / save fn)")
    if (not has_wkb_in_col_map) and (not is_geom_config) and used_df_save:
        report.ok("非 geometry 全鏈路一致")

    # 偵測硬編 token / 信箱
    src_lower = src.lower()
    suspicious_patterns = [
        (r'token\s*=\s*["\'][a-z0-9\-_]{16,}["\']', "硬編 token"),
        (r'api[_-]?key\s*=\s*["\'][a-z0-9\-_]{16,}["\']', "硬編 api_key"),
        (r'authorization["\']\s*:\s*["\']bearer\s+[a-z0-9\-_\.]+["\']', "硬編 Bearer token"),
    ]
    for pat, label in suspicious_patterns:
        if re.search(pat, src_lower):
            report.fail(f"偵測到{label}(請改走 Airflow Variable / Connection)")

    # 規則 A:嚴禁爬蟲
    scraping_libs = [
        ("BeautifulSoup / bs4", r"\bfrom\s+bs4\b|\bimport\s+bs4\b|\bBeautifulSoup\s*\("),
        ("selenium", r"\bfrom\s+selenium\b|\bimport\s+selenium\b"),
        ("lxml.html", r"\bfrom\s+lxml\s*\.\s*html\b|\blxml\.html\b"),
        ("playwright", r"\bfrom\s+playwright\b|\bimport\s+playwright\b"),
        ("scrapy", r"\bfrom\s+scrapy\b|\bimport\s+scrapy\b"),
    ]
    for lib_name, pat in scraping_libs:
        if re.search(pat, src):
            report.fail(
                f"偵測到爬蟲庫 {lib_name}(本 toolkit 嚴禁爬蟲;請改用結構化資料 API,或聯絡資料擁有單位)"
            )

    # 規則 C:Custom inline requests 健全性 — 若用 requests.get/post 等,必須有 timeout 與 raise_for_status
    if re.search(r"\brequests\s*\.\s*(get|post|put|delete|head|patch)\s*\(", src):
        if not re.search(r"timeout\s*=", src):
            report.fail(
                "偵測到 inline requests 但無 `timeout=` 參數(必填,避免 task 卡死)"
            )
        else:
            report.ok("inline requests 含 timeout")
        if not re.search(r"\.\s*raise_for_status\s*\(\s*\)", src):
            report.fail(
                "偵測到 inline requests 但無 `.raise_for_status()`(必填,捕捉 HTTP 錯誤)"
            )
        else:
            report.ok("inline requests 含 raise_for_status()")
        report.warn(
            "本 DAG 使用 inline requests:請於 commit 訊息加 `[needs-helper-review]` 標籤,並在 PR description 通知維護者(規則 C)"
        )

    return {
        "col_map": col_map,
        "is_geometry_in_py": has_wkb_in_col_map,
    }


def _check_test_file(test_file: Path, table_name: str, config: dict, report: Report) -> None:
    """test_<table_name>.py 必須真的測 source URL,不能空殼。"""
    src = test_file.read_text(encoding="utf-8")

    # 必含對 requests / urlopen 的呼叫
    has_request_call = bool(
        re.search(r"\brequests\s*\.\s*(get|post|head)\s*\(", src)
        or re.search(r"\burlopen\s*\(", src)
    )
    if not has_request_call:
        report.fail(
            f"{test_file.name} 沒有對 source URL 的 HTTP 請求(必須真的打到 URL,不可空殼通過)"
        )
    else:
        report.ok(f"{test_file.name} 含對 source URL 的請求")

    # 必含 timeout 與 raise_for_status(若用 requests)
    if re.search(r"\brequests\s*\.\s*(get|post|head)\s*\(", src):
        if not re.search(r"timeout\s*=", src):
            report.fail(f"{test_file.name} 的 requests 缺 timeout=")
        if not re.search(r"\.\s*raise_for_status\s*\(\s*\)", src):
            report.fail(f"{test_file.name} 的 requests 缺 .raise_for_status()")

    # source_type dispatch 必須對應到 config 內的 source_type
    config_source_type = config.get("data_infos", {}).get("source_type", "")
    if config_source_type and config_source_type not in src:
        report.warn(
            f"{test_file.name} 內未明確處理 source_type='{config_source_type}'(可能走 fallback,確認是否預期)"
        )

    # 必須含「真實打 URL 的測試函式」 — 至少一個 def test_*
    if not re.search(r"\bdef\s+test_\w+\s*\(", src):
        report.fail(f"{test_file.name} 沒有 `def test_*` 函式(命名以 test_ 開頭便於 pytest)")
    else:
        report.ok(f"{test_file.name} 含 test_* 函式")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    dag_dir = Path(sys.argv[1]).resolve()
    if not dag_dir.is_dir():
        print(f"ERROR: {dag_dir} 不是目錄", file=sys.stderr)
        return 2

    table_name = dag_dir.name
    proj_folder = dag_dir.parent.name

    print(f"驗證 DAG: {proj_folder}/{table_name}")
    print(f"路徑: {dag_dir}\n")

    report = Report()

    files = _check_files_exist(dag_dir, table_name, report)
    if files is None:
        print(report.render())
        return 1

    config = _check_config(files["config"], table_name, report)
    if config is None:
        print(report.render())
        return 1

    _check_py(files["py"], table_name, proj_folder, config, report)
    _check_test_file(files["test"], table_name, config, report)

    print(report.render())
    return 1 if report.fails else 0


if __name__ == "__main__":
    sys.exit(main())
