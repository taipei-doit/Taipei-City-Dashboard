"""
gen_config.py
=============
輸入中文資料集名稱，自動查詢 CSV、呼叫 API 取得真實欄位，
產出 config 並直接寫入 etl_config.json。
rename_map 的英文欄位名以 col_1, col_2... 佔位，請手動修改。

用法：
    python gen_config.py
    python gen_config.py 臺北市醫院清冊
    python gen_config.py 新北市文化資產 --dag-id ntpc_heritage

需要：
    pip install requests pandas
"""

import os
import re
import sys
import json
import argparse

import requests
import urllib3
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_HERE        = os.path.dirname(os.path.abspath(__file__))
_DE_ROOT     = os.path.abspath(os.path.join(_HERE, "..", ".."))
CONFIG_PATH  = os.path.join(_HERE, "etl_config.json")

CSV_FILES = {
    "open_data": os.path.join(_DE_ROOT, "Open Data.csv"),
    "open_api":  os.path.join(_DE_ROOT, "Open API.csv"),
    "data_list": os.path.join(_DE_ROOT, "dataList.csv"),
}

TAIPEI_BASE = "https://data.taipei/api/v1/dataset"
NTPC_BASE   = "https://data.ntpc.gov.tw/api/datasets"


# ─────────────────────────────────────────────
# Step 1: 從 CSV 找到 PAGE_ID、RID、source_dept
# ─────────────────────────────────────────────
_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)

def _parse_rid_from_url(access_url: str) -> str:
    for url in access_url.split(","):
        url = url.strip()
        parts = url.strip("/").split("/")
        # 優先：/resource/{RID}
        if "resource" in parts:
            idx = parts.index("resource")
            if idx + 1 < len(parts):
                candidate = parts[idx + 1].split("?")[0]
                if _UUID_RE.match(candidate):
                    return candidate
        # 次選：/dataset/{RID} (data.taipei API 格式)
        for seg in ("dataset",):
            if seg in parts:
                idx = parts.index(seg)
                if idx + 1 < len(parts):
                    candidate = parts[idx + 1].split("?")[0]
                    if _UUID_RE.match(candidate):
                        return candidate
        # 最後：URL 中第一個符合 UUID 格式的片段
        m = _UUID_RE.search(url)
        if m:
            return m.group(0)
    return ""


def lookup_in_csv(keyword: str) -> dict:
    for csv_type, path in CSV_FILES.items():
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, encoding="utf-8-sig")
        name_col = "資料集名稱"
        if name_col not in df.columns:
            continue
        matches = df[df[name_col].str.contains(keyword, na=False)]
        if matches.empty:
            continue

        row       = matches.iloc[0]
        full_name = str(row[name_col]).strip()
        dept      = str(row.get("資料集提供機關", row.get("資料集提供機關名稱", ""))).strip()

        if csv_type == "open_data":
            page_id     = str(row.get("資料集id", "")).strip()
            access_url  = str(row.get("資料存取網址", "")).strip()
            rid         = _parse_rid_from_url(access_url)
            source_type = "data.taipei API"
        elif csv_type == "open_api":
            page_id     = ""
            rid         = ""
            source_type = "open_api"
        else:  # data_list
            dataset_url = str(row.get("資料集網址", "")).strip()
            ntpc_id     = str(row.get("識別碼", "")).strip().lower()
            if "data.ntpc.gov.tw" in dataset_url:
                page_id     = ntpc_id
                rid         = ""
                source_type = "data.ntpc API"
            else:
                page_id     = ntpc_id
                rid         = ""
                source_type = "other"

        print(f"[CSV] 找到資料集：{full_name}（來源：{csv_type}，source_type：{source_type}）")
        return {
            "full_name":   full_name,
            "source_dept": dept,
            "source_type": source_type,
            "RID":         rid,
            "PAGE_ID":     page_id,
        }

    raise ValueError(f"在所有 CSV 中找不到「{keyword}」，請確認名稱是否正確。")


# ─────────────────────────────────────────────
# Step 2: 從 API 取得真實欄位
# ─────────────────────────────────────────────
def fetch_columns(meta: dict) -> list[str]:
    skip = {"_id", "_importdate", "objectid"}

    if meta["source_type"] == "data.taipei API" and meta["RID"]:
        url    = f"{TAIPEI_BASE}/{meta['RID']}"
        params = {"scope": "resourceAquire", "limit": 1, "offset": 0}
        resp   = requests.get(url, params=params, timeout=30, verify=False)
        resp.raise_for_status()
        data    = resp.json()
        results = data if isinstance(data, list) else data.get("result", {}).get("results", [])
        if not results:
            print("[警告] data.taipei API 回傳空資料。")
            return []
        cols = [k for k in results[0].keys() if k.lower() not in skip]

    elif meta["source_type"] == "data.ntpc API" and meta["PAGE_ID"]:
        url  = f"{NTPC_BASE}/{meta['PAGE_ID']}/json"
        resp = requests.get(url, params={"limit": 1, "offset": 0}, timeout=30, verify=False)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            print("[警告] NTPC API 回傳空資料。")
            return []
        cols = [k for k in results[0].keys() if k.lower() not in skip]

    else:
        print("[警告] 無法自動取得欄位（無 RID/PAGE_ID 或 source_type 不支援）。")
        return []

    print(f"[API] 取得欄位：{cols}")
    return cols


# ─────────────────────────────────────────────
# Step 3: 寫入 etl_config.json
# ─────────────────────────────────────────────
def save_to_json(dag_id: str, meta: dict, cols: list[str]):
    keep_cols = ["data_time"] + cols

    entry = {
        "dag_id":       dag_id,
        "output_table": dag_id,
        "source_dept":  meta["source_dept"],
        "source_type":  meta["source_type"],
        "RID":          meta["RID"],
        "PAGE_ID":      meta["PAGE_ID"],
        "keep_cols":    keep_cols,
    }

    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            content = f.read().strip()
        config = json.loads(content) if content else {"_default": ""}
    except (FileNotFoundError, json.JSONDecodeError):
        config = {"_default": ""}

    if dag_id in config:
        overwrite = input(f"[警告] dag_id「{dag_id}」已存在，覆蓋？(y/N)：").strip().lower()
        if overwrite != "y":
            print("已取消。")
            return

    config[dag_id] = entry

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"[完成] 已寫入 etl_config.json → \"{dag_id}\"")
    print(f"       rename_map 欄位名為佔位符（col_1, col_2...），請手動修改。")


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="自動產出並寫入 etl_config.json")
    parser.add_argument("keyword",  nargs="?", default="", help="資料集中文名稱關鍵字")
    parser.add_argument("--dag-id", default="",            help="自訂英文 dag_id")
    args = parser.parse_args()

    keyword = args.keyword or input("請輸入資料集名稱關鍵字（中文）：").strip()
    if not keyword:
        print("[錯誤] 請提供關鍵字。")
        sys.exit(1)

    meta   = lookup_in_csv(keyword)
    dag_id = args.dag_id or input(
        f"請輸入 dag_id（英文 snake_case，Enter 略過）：[{keyword.replace(' ', '_')}] "
    ).strip() or keyword.replace(" ", "_")
    dag_id = re.sub(r"[^\w]", "_", dag_id).lower()

    cols = fetch_columns(meta)

    save_to_json(dag_id, meta, cols)


if __name__ == "__main__":
    main()
