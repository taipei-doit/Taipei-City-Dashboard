FROM apache/airflow:3.2.0
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         gdal-bin libgdal-dev build-essential \
		 vim curl wget \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements.txt /tmp/
RUN  pip install \
       --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.2.0/constraints-3.12.txt" \
       -r /tmp/requirements.txt

