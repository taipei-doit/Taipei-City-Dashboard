"""
duckdb_export_helper.py

DuckDB Parquet 匯出組合層。
組合 Trino 查詢、OMD dtype mapping、upload_parquet_to_minio 三個工具，
提供單一入口供 DAG 呼叫，使用方式類似 DataCache。

路徑規範：
  - Bucket：duckdb-files
  - Object：abfs/dal/v_{dag_name_lowercase}.parquet
"""
import logging
import os
from typing import Dict

import pandas as pd
from sqlalchemy import text

from sqlalchemy import create_engine
from sqlalchemy.schema import Table, MetaData
from sqlalchemy.sql.expression import select, text
from trino.auth import BasicAuthentication
#from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

class Trino:

    engine = None
    def __init__(self,
            username: str,
            passwd: str,
            host: str,
            port: str,
            ssl_cert_path: str,
            conn_pool_size: int = 20,
            pool_pre_ping: bool = False,
            debug:bool = False,
            query_max_run_time: str = None
            
        ):

        self.username = username
        self.passwd = passwd
        self.host = host
        self.port = port
        self.ssl_cert_path = ssl_cert_path
        self.conn_pool_size = conn_pool_size
        self.pool_pre_ping = pool_pre_ping
        self.debug = debug
        self.query_max_run_time = query_max_run_time

    def custom_args(self):
        connect_args={
            "auth": BasicAuthentication(self.username, self.passwd),
            "http_scheme": "https",
            "verify": self.ssl_cert_path,
            "session_properties": {"query_max_run_time": self.query_max_run_time},
        }
        return connect_args

    def connect(self):
        if self.engine is None:
            if self.query_max_run_time:
                connect_args = self.custom_args()
            else:
                connect_args={
                    "auth": BasicAuthentication(self.username, self.passwd),
                    "http_scheme": "https",
                    "verify": self.ssl_cert_path,
                }
            self.engine = create_engine(
                f"trino://{self.username}@{self.host}:{self.port}",
                connect_args=connect_args,
                pool_size=int(self.conn_pool_size * 0.8) if self.conn_pool_size is not None else 20,
                max_overflow=int(self.conn_pool_size * 0.2) if self.conn_pool_size is not None else 4,
                pool_pre_ping=self.pool_pre_ping,
                echo_pool=None if not self.debug else "debug",
            )
            # SQLAlchemyInstrumentor().instrument(
            #     engine=self.engine,
            # )

        return self.engine.connect()
    



# OMD dataType → pandas dtype
_OMD_TYPE_MAP = {
    "VARCHAR": "object",
    "CHAR": "object",
    "TEXT": "object",
    "STRING": "object",
    "JSON": "object",
    "INT": "Int64",
    "INTEGER": "Int64",
    "BIGINT": "Int64",
    "SMALLINT": "Int16",
    "TINYINT": "Int8",
    "FLOAT": "float64",
    "DOUBLE": "float64",
    "REAL": "float32",
    "NUMERIC": "float64",
    "DECIMAL": "float64",
    "BOOLEAN": "boolean",
    "BINARY": "object",
    "TIMESTAMP": "datetime64",
    "DATE": "date32",
    "DATETIME": "datetime64",
    "TIME": "time64",
}


def _get_trino_server(
    trino_user: str,
    trino_pass: str,
    trino_host: str,
    trino_port: str = "8443",
    trino_ssl_cert: str = "",
) -> Trino:
    """建立 Trino 連線（可本地端使用，不依賴 Airflow Variable）。"""
    return Trino(
        username=trino_user,
        passwd=trino_pass,
        host=trino_host,
        port=trino_port,
        ssl_cert_path=trino_ssl_cert,
        conn_pool_size=5,
        pool_pre_ping=True,
    )


def _get_view_schema(
    omd_url: str, omd_token: str, omd_fqn: str
) -> Dict[str, str]:
    """
    從 OMD 查詢 View 欄位 dtype mapping（可本地端使用）。

    :param omd_url: OMD API base URL
    :param omd_token: OMD Bearer token
    :param omd_fqn: OMD 完整路徑，例如 'Trino.abfs.dal.v_stg_tdx_alert'
    :return: {欄位名: pandas dtype}
    """
    import requests

    headers = {"Authorization": omd_token, "content-type": "application/json"}
    url = f"{omd_url}/tables/name/{omd_fqn}?fields=tableConstraints"
    rs = requests.get(url=url, headers=headers, timeout=30)
    if rs.status_code != 200:
        raise ValueError(f"[DuckDBExport] OMD 查詢失敗：{omd_fqn}（status={rs.status_code}）")

    cols_info = rs.json()["columns"]
    return {
        col["name"]: _OMD_TYPE_MAP.get(col["dataType"].upper(), "object")
        for col in cols_info
    }


def _apply_dtypes(df: pd.DataFrame, dtypes: Dict[str, str]) -> pd.DataFrame:
    """將 OMD dtype mapping 套用到 DataFrame。"""
    # OMD 有但 Trino 沒有的欄位，先補 NULL 欄位
    for col, dtype in dtypes.items():
        if col not in df.columns:
            if dtype == "object":
                df[col] = pd.Series(dtype="string")
            elif dtype in ("Int64", "Int16", "Int8"):
                df[col] = pd.Series(dtype=dtype)
            elif dtype in ("float64", "float32"):
                df[col] = pd.Series(dtype=dtype)
            elif dtype == "boolean":
                df[col] = pd.Series(dtype="boolean")
            elif dtype == "datetime64":
                df[col] = pd.Series(dtype="datetime64[ms]")
            elif dtype in ("date32", "time64"):
                df[col] = pd.Series(dtype="object")
            else:
                df[col] = pd.Series(dtype="object")
            logging.warning(f"[DuckDBExport] 補齊 OMD 欄位（Trino 缺少）：{col} ({dtype})")

    # 型別轉換
    for col, dtype in dtypes.items():
        if col not in df.columns:
            continue
        try:
            if dtype == "object":
                df[col] = df[col].astype("string")
            elif dtype in ("Int64", "Int16", "Int8"):
                df[col] = pd.to_numeric(df[col], errors="coerce").astype(dtype)
            elif dtype in ("float64", "float32"):
                df[col] = pd.to_numeric(df[col], errors="coerce").astype(dtype)
            elif dtype == "boolean":
                if df[col].dtype != bool:
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype(bool)
            elif dtype == "datetime64":
                df[col] = pd.to_datetime(df[col], errors="coerce")
            elif dtype == "date32":
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
            elif dtype == "time64":
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.time
        except Exception as cast_err:
            logging.warning(f"[DuckDBExport] 欄位 {col} 轉型 {dtype} 失敗，保留原型別：{cast_err}")
    return df
    


class DuckDBExport:
    """
    DuckDB Parquet 匯出，單行呼叫即完成 Trino 查詢 → Parquet → MinIO 全流程。

    欄位順序與型別：欄位順序從 Trino 取得（與 OMD 一致），型別從 OMD 查詢。

    使用範例（在 Redis cache 前）：
        DuckDBExport(output_table, etl_dtm)

    :param output_table: 資料表名稱（例如 'STG_TDX_ALERT'）
    :param etl_dtm: ETL 執行時間
    :param bucket: MinIO bucket 名稱（預設 'duckdb-files'）
    """

    def __init__(
        self,
        output_table: str,
        etl_dtm,
        bucket: str = "duckdb-files",
    ):
        # Lazy import — 只在 Airflow 環境下才會用到
        from airflow.models import Variable
        from utils.helper.minio_helper import upload_parquet_to_minio

        if Variable.get("enable_duckdb_export", default_var="false").lower() != "true":
            logging.warning(f"[DuckDBExport] 已關閉（enable_duckdb_export != true），跳過：{output_table}")
            return

        trino_view = f"abfs.dal.v_{output_table.lower()}"
        omd_fqn = f"Trino.{trino_view}"
        parquet_path = f"/tmp/v_{output_table.lower()}.parquet"
        object_name = f"abfs/dal/v_{output_table.lower()}.parquet"

        logging.warning(f"[DuckDBExport] 開始匯出：{output_table}")

        omd_url = Variable.get("omd_url")
        omd_token = Variable.get("omd_token")
        dtypes = _get_view_schema(omd_url, omd_token, omd_fqn)
        logging.warning(f"[DuckDBExport] OMD dtype 查詢完成（{len(dtypes)} 欄）")

        trino_user = Variable.get("TRINO_USERNAME")
        trino_pass = Variable.get("TRINO_PASSWD")
        trino_host = Variable.get("TRINO_HOST")
        trino_port = Variable.get("TRINO_PORT", "8443")
        trino_ssl_cert = Variable.get("TRINO_SSL_CERT_PATH")
        trino = _get_trino_server(trino_user, trino_pass, trino_host, trino_port, trino_ssl_cert)
        with trino.connect() as conn:
            df = pd.read_sql(text(f"SELECT * FROM {trino_view}"), conn)
        logging.warning(f"[DuckDBExport] Trino 查詢完成（{len(df)} 列）")

        # 統一欄位名稱為小寫（OMD 和 Trino 可能回傳大寫欄位名）
        dtypes = {k.lower(): v for k, v in dtypes.items()}
        df.columns = df.columns.str.lower()

        df = _apply_dtypes(df, dtypes)
        logging.warning(f"[DuckDBExport] df columns: {df.columns.tolist()}")
        df.to_parquet(parquet_path, engine="pyarrow", index=False)
        logging.warning(f"[DuckDBExport] Parquet 完成：{parquet_path}")

        upload_parquet_to_minio(
            local_parquet_path=parquet_path,
            bucket=bucket,
            object_name=object_name,
            etl_dtm=etl_dtm,
        )
        logging.warning(f"[DuckDBExport] 完成：s3://{bucket}/{object_name}")

        if os.path.exists(parquet_path):
            os.remove(parquet_path)
            logging.warning(f"[DuckDBExport] 暫存檔已刪除：{parquet_path}")