"""
gen_config.py
=============
輸入中文資料集名稱，自動查詢 CSV、呼叫 API 取得真實欄位，
產出 config 並直接寫入 etl_config.json。

用法：
    python gen_config.py
    python gen_config.py 臺北市醫院清冊
    python gen_config.py 消防局EOC --dag-id eoc_shelter
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

_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)


# ─────────────────────────────────────────────
# 工具函式
# ─────────────────────────────────────────────

def _parse_rid_from_url(access_url: str) -> str:
    for url in access_url.split(","):
        url = url.strip()
        parts = url.strip("/").split("/")
        if "resource" in parts:
            idx = parts.index("resource")
            if idx + 1 < len(parts):
                candidate = parts[idx + 1].split("?")[0]
                if _UUID_RE.match(candidate):
                    return candidate
        for seg in ("dataset",):
            if seg in parts:
                idx = parts.index(seg)
                if idx + 1 < len(parts):
                    candidate = parts[idx + 1].split("?")[0]
                    if _UUID_RE.match(candidate):
                        return candidate
        m = _UUID_RE.search(url)
        if m:
            return m.group(0)
    return ""


def _extract_open_api_endpoints(row: pd.Series) -> list[dict]:
    """
    掃描 Open API CSV 的一列，找出所有 HTTP 端點。
    回傳 [{"url": ..., "method": ..., "desc": ...}, ...]
    """
    values = row.tolist()
    col_names = list(row.index)

    # 先找出所有 URL 欄位的位置
    url_indices = [
        i for i, v in enumerate(values)
        if isinstance(v, str) and v.strip().lower().startswith("http")
    ]

    # HTTP method（GET/POST）候選：URL 欄位左邊可能有 method 欄位
    http_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}

    endpoints = []
    for idx in url_indices:
        url = values[idx].strip()

        # 向左掃找最近的 GET/POST
        method = "GET"
        for offset in range(1, min(idx + 1, 10)):
            candidate = str(values[idx - offset]).strip().upper()
            if candidate in http_methods:
                method = candidate
                break

        # 向左掃找最近的描述（非空、非 GET/POST、非 URL）
        desc = ""
        for offset in range(1, min(idx + 1, 15)):
            v = str(values[idx - offset]).strip()
            if (v and v.upper() not in http_methods
                    and not v.lower().startswith("http")
                    and v.lower() not in ("nan", "")):
                desc = v
                break

        endpoints.append({"url": url, "method": method, "desc": desc,
                           "col_name": col_names[idx]})

    return endpoints


def _choose_endpoint(endpoints: list[dict]) -> dict:
    """多個端點時讓使用者選一個。"""
    if len(endpoints) == 1:
        print(f"[API] 找到端點：{endpoints[0]['method']} {endpoints[0]['url']}")
        return endpoints[0]

    print(f"\n[API] 找到 {len(endpoints)} 個端點，請選擇：")
    for i, ep in enumerate(endpoints):
        print(f"  [{i}] {ep['method']:4s}  {ep['desc']}")
        print(f"        {ep['url']}")
    choice = input(f"輸入編號 [0-{len(endpoints)-1}]，Enter 選 0：").strip()
    idx = int(choice) if choice.isdigit() and int(choice) < len(endpoints) else 0
    return endpoints[idx]


# ─────────────────────────────────────────────
# Step 1: 從 CSV 找到資料集 meta
# ─────────────────────────────────────────────

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
            api_url     = ""
            api_method  = "GET"

        elif csv_type == "open_api":
            # 掃描所有 URL 欄位
            endpoints = _extract_open_api_endpoints(row)
            if not endpoints:
                print(f"[警告] Open API CSV 中找不到有效 URL，請手動填入 api_url。")
                endpoints = [{"url": "", "method": "GET", "desc": ""}]

            chosen     = _choose_endpoint(endpoints)
            api_url    = chosen["url"]
            api_method = chosen["method"]
            page_id    = ""
            rid        = ""
            source_type = "open_api" if api_method == "GET" else "open_api_post"

        else:  # data_list
            dataset_url = str(row.get("資料集網址", "")).strip()
            ntpc_id     = str(row.get("識別碼", "")).strip().lower()
            api_url     = ""
            api_method  = "GET"
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
            "api_url":     api_url,
            "api_method":  api_method,
        }

    raise ValueError(f"在所有 CSV 中找不到「{keyword}」，請確認名稱是否正確。")


# ─────────────────────────────────────────────
# Step 2: 從 API 取得真實欄位
# ─────────────────────────────────────────────

def fetch_columns(meta: dict) -> list[str]:
    skip = {"_id", "_importdate", "objectid"}

    source_type = meta["source_type"]

    if source_type == "data.taipei API" and meta["RID"]:
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

    elif source_type == "data.ntpc API" and meta["PAGE_ID"]:
        url  = f"{NTPC_BASE}/{meta['PAGE_ID']}/json"
        resp = requests.get(url, params={"limit": 1, "offset": 0}, timeout=30, verify=False)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            print("[警告] NTPC API 回傳空資料。")
            return []
        cols = [k for k in results[0].keys() if k.lower() not in skip]

    elif source_type in ("open_api", "open_api_post") and meta.get("api_url"):
        try:
            if source_type == "open_api_post":
                resp = requests.post(meta["api_url"], json={},
                                     headers={"Content-Type": "application/json"},
                                     timeout=30, verify=False)
            else:
                resp = requests.get(meta["api_url"], timeout=30, verify=False)
            resp.raise_for_status()
            data = resp.json()

            # 嘗試找出 list 結構
            records = None
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                for key in ("result", "data", "results", "records", "DATA", "Result"):
                    if key in data and isinstance(data[key], list):
                        records = data[key]
                        break
                if records is None:
                    records = [data]

            if records and isinstance(records[0], dict):
                cols = [k for k in records[0].keys() if k.lower() not in skip]
            else:
                print("[警告] Open API 回傳格式無法自動解析欄位。")
                return []
        except Exception as e:
            print(f"[警告] Open API 呼叫失敗（{e}），欄位留空。")
            return []

    else:
        print("[警告] 無法自動取得欄位（無 RID/PAGE_ID/api_url 或 source_type 不支援）。")
        return []

    print(f"[API] 取得欄位：{cols}")
    return cols


# ─────────────────────────────────────────────
# Step 3: 寫入 etl_config.json
# ─────────────────────────────────────────────

def save_to_json(dag_id: str, meta: dict, cols: list[str]):
    keep_cols = ["data_time"] + cols

    entry: dict = {
        "dag_id":       dag_id,
        "output_table": dag_id,
        "source_dept":  meta["source_dept"],
        "source_type":  meta["source_type"],
        "keep_cols":    keep_cols,
    }

    # open_api / open_api_post：存 api_url（+ api_body for POST）
    if meta["source_type"] in ("open_api", "open_api_post"):
        entry["api_url"] = meta.get("api_url", "")
        if meta["source_type"] == "open_api_post":
            entry["api_body"] = {}
    else:
        entry["RID"]     = meta["RID"]
        entry["PAGE_ID"] = meta["PAGE_ID"]

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
    if meta["source_type"] in ("open_api", "open_api_post"):
        print(f"       api_url：{entry['api_url']}")
    print(f"       keep_cols 已自動填入，可依需求刪減欄位。")


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="自動產出並寫入 etl_config.json")
    parser.add_argument("keyword",  nargs="?", default="", help="資料集中文名稱關鍵字")
    parser.add_argument("--dag-id", default="",            help="自訂 dag_id（中英文均可）")
    args = parser.parse_args()

    keyword = args.keyword or input("請輸入資料集名稱關鍵字（中文）：").strip()
    if not keyword:
        print("[錯誤] 請提供關鍵字。")
        sys.exit(1)

    meta   = lookup_in_csv(keyword)
    dag_id = args.dag_id or input(
        f"請輸入 dag_id（Enter 使用預設「{keyword}」）：[{keyword}] "
    ).strip() or keyword
    dag_id = re.sub(r"[^\w一-鿿]", "_", dag_id)

    cols = fetch_columns(meta)

    save_to_json(dag_id, meta, cols)


if __name__ == "__main__":
    main()
