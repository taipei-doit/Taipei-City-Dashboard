"""
extract/臺北市食品衛生管理查驗工作.py
======================================
從 tsis.dbas.gov.taipei 下載兩段年份的食品衛生查驗統計 CSV，
合併後統一欄位命名（去除 [件][%]，斜線換底線）。
"""

import requests
import urllib3
import pandas as pd
from io import StringIO

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_URLS = [
    # 民國 81~94 年
    (
        "https://tsis.dbas.gov.taipei/statis/webMain.aspx"
        "?sys=220&ymf=8100&ymt=9400&kind=21&type=0&funid=a05032001"
        "&cycle=4&outmode=12&compmode=0&outkind=1&deflst=2&nzo=1"
    ),
    # 民國 95 年至今
    (
        "https://tsis.dbas.gov.taipei/statis/webMain.aspx"
        "?sys=220&ymf=9500&kind=21&type=0&funid=a05032002"
        "&cycle=4&outmode=12&compmode=0&outkind=1&deflst=2&nzo=1"
    ),
]


def extract(config: dict) -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0"}
    dfs = []

    for url in _URLS:
        resp = requests.get(url, headers=headers, timeout=30, verify=False)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.content.decode("utf-8-sig")))
        print(f"[Extract] 食品衛生查驗：取得 {len(df)} 筆")
        dfs.append(df)

    combined = pd.concat(dfs, axis=0, ignore_index=True, join="outer")

    combined.columns = (
        combined.columns
        .str.replace(r"\[.*?\]", "", regex=True)
        .str.replace("/", "_", regex=False)
        .str.strip()
    )
    combined = combined.rename(columns={"統計期": "data_time"})
    combined = combined.sort_values("data_time").reset_index(drop=True)

    print(f"[Extract] 食品衛生查驗合併完成：共 {len(combined)} 筆")
    return combined
