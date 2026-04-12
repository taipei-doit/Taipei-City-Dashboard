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
RUN  PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')") && \
     pip install \
       --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.2.0/constraints-${PYTHON_VERSION}.txt" \
       -r /tmp/requirements.txt

