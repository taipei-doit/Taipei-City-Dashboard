FROM apache/airflow:2.10.5
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
RUN  pip install -r /tmp/requirements.txt 

