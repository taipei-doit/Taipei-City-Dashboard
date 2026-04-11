# Custom Windmill worker image: base 上補 GIS / Postgres 系統依賴 + ETL adapter 層
FROM ghcr.io/windmill-labs/windmill:main

USER root

# Windmill base image 是 debian，補上 geopandas / shapely / psycopg2 需要的 shared libs
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgdal32 gdal-bin \
        libgeos-c1v5 \
        libproj25 \
        libpq5 \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV TZ=Asia/Taipei

# 把 adapter 層烤進 image，Python script 透過 PYTHONPATH=/opt/adapters import
COPY adapters /opt/adapters

ENV PYTHONPATH="/opt/adapters:/opt/airflow/dags"
ENV DAG_PATH=/opt/airflow/dags
ENV DATA_PATH=/opt/airflow/data

# 不覆蓋 Windmill 原本的 ENTRYPOINT / CMD，讓 MODE=worker env 決定行為
