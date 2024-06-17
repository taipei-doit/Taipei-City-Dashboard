import os
from ast import literal_eval

from airflow.configuration import conf
from airflow.models import Variable

DAG_PATH = conf.get("core", "dags_folder")
DATA_PATH = os.path.join(DAG_PATH, "..", "data")
PLUGIN_PATH = conf.get("core", "plugins_folder")
HTTPS_PROXY_ENABLED = Variable.get("HTTPS_PROXY_ENABLED", "false").lower() == "true"
if HTTPS_PROXY_ENABLED:
    proxies = literal_eval(Variable.get("PROXY_URL"))
    PROXIES = {"http": proxies["https"], "https": proxies["https"]}
else:
    PROXIES = None
