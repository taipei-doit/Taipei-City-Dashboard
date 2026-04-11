FROM python:3.11-slim

# GIS / Postgres system libs 供 geopandas / shapely / psycopg2 使用
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgdal32 gdal-bin \
        libgeos-c1v5 \
        libproj25 \
        libpq5 \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV TZ=Asia/Taipei

# 與現有 DE 相容的核心 Python 依賴（PoC 範圍，之後可擴充）
RUN pip install --no-cache-dir \
        pandas==2.2.3 \
        geopandas==0.14.4 \
        shapely==2.0.5 \
        geoalchemy2==0.15.2 \
        sqlalchemy==2.0.32 \
        psycopg2-binary==2.9.9 \
        requests==2.32.3 \
        numpy==1.26.4

# 把 adapter 層烤進 image；/opt/airflow/dags 會在執行時由 Kestra bind-mount 掛入
COPY adapters /opt/adapters

ENV PYTHONPATH="/opt/adapters:/opt/airflow/dags"
ENV DAG_PATH=/opt/airflow/dags
ENV DATA_PATH=/opt/airflow/data

WORKDIR /opt
