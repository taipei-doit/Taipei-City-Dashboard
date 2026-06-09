#!/usr/bin/env python3
"""
Trino → Parquet 自動化匯出工具（本地端使用）- 支援批次處理

用法：
    python trino_to_parquet.py <view1> <view2> <view3>
    python trino_to_parquet.py v_stg_tdx_route v_stg_tdx_alert --limit 100

範例：
    python trino_to_parquet.py v_stg_cwa_weather_7d v_stg_ibus_gateway
"""

import os
import sys
import argparse
import logging
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from asdf import _get_trino_server, _get_view_schema, _apply_dtypes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── 主程式 ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Trino → Parquet 匯出工具（批次版）")
    # 修改處：nargs="+" 代表可以接受一個或多個參數，並將其轉為 list
    parser.add_argument("views", nargs="+", help="Trino view 名稱列表，例如 v_stg_tdx_route v_stg_tdx_alert")
    parser.add_argument("--output_dir", "-d", default="./", help="輸出目錄（預設：當前目錄）")
    parser.add_argument("--catalog", default="abfs.dal", help="Trino catalog（預設：abfs.dal）")
    parser.add_argument("--limit", type=int, default=None, help="LIMIT 行數（預設：全部）")
    parser.add_argument("--no-omd", action="store_true", help="不使用 OMD schema")
    parser.add_argument("--show", action="store_true", help="顯示 DataFrame 內容")
    args = parser.parse_args()

    # 初始化 Trino 連線（放在迴圈外，避免重複連線）
    from sqlalchemy import text
    trino = _get_trino_server(
        trino_user="airflow",
        trino_pass="eiv5Yiebo3OSieL_",
        trino_host="trino.prod.datacenter.com",
        trino_port=	8443,
        trino_ssl_cert=os.getenv("TRINO_SSL_CERT", ""),
    )

    # 批次處理迴圈
    for view_name in args.views:
        try:
            if view_name.startswith("v_"):
                full_view = f"{args.catalog}.{view_name}"
            else:
                full_view = f"{args.catalog}.v_{view_name}"

            omd_fqn = f"Trino.{full_view}"
            output_view_name = view_name if view_name.startswith("v_") else f"v_{view_name}"
            output_path = Path(args.output_dir) / f"{output_view_name}.parquet"

            log.info(f"[{view_name}] 開始處理...")
            log.info(f"輸出路徑：{output_path}")

            # OMD schema 獲取
            dtypes = {}
            if not args.no_omd:
                omd_url = os.getenv("OMD_URL", "").rstrip("/")
                omd_token = os.getenv("OMD_TOKEN", "")
                if omd_url and omd_token:
                    dtypes = _get_view_schema(omd_url, omd_token, omd_fqn)

            # Trino 查詢
            with trino.connect() as conn:
                query = f"SELECT * FROM {full_view}"
                if args.limit:
                    query += f" LIMIT {args.limit}"
                log.info(f"執行查詢：{query}")
                df = pd.read_sql(text(query), conn)

            if df.empty:
                log.warning(f"[{view_name}] 查無資料，跳過。")
                continue

            # 轉換與寫入
            if dtypes:
                dtypes_lower = {k.lower(): v for k, v in dtypes.items()}
                df.columns = df.columns.str.lower()
                df = _apply_dtypes(df, dtypes_lower)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(str(output_path), engine="pyarrow", index=False)
            log.info(f"[{view_name}] 匯出完成！大小: {output_path.stat().st_size / 1024:.1f} KB")

            if args.show:
                print(df.head())

        except Exception as e:
            log.error(f"處理 {view_name} 時發生錯誤: {str(e)}")
            continue

if __name__ == "__main__":
    main()