import json
import os
from ast import literal_eval
from datetime import datetime

from airflow import DAG
from airflow.models import Variable
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from settings.global_config import DAG_PATH, DATA_PATH, PROXIES
from sqlalchemy import create_engine
from sqlalchemy.sql import text as sa_text
from utils.get_time import get_tpe_now_time


def _read_config(path, file_name="job_config.json"):
    """
    Read DAG's config from the `job_config.json` file.
    """
    file_path = os.path.join(path, file_name)
    with open(file_path, "r", encoding="utf-8") as json_file:
        config_dict = json.load(json_file)

    print(f"Read config successfully from {file_path}.")
    return config_dict


def _validate_config(config_dict):
    """
    Raise an error if the config is empty or necessary keys are missing.
    """
    is_empty = not bool(config_dict)
    if is_empty:
        raise ValueError("Config is empty. Please check the config file.")

    # Check necessary keys
    # dag_infos part
    dag_infos = config_dict.get("dag_infos")
    if not bool(dag_infos):
        raise KeyError("Necessary part `dag_infos` is missing.")
    # dag_infos keys
    dag_infos_necessary_keys = [
        "dag_id",
        "start_date",
        "schedule_interval",
        "catchup",
        "tags",
        "default_args",
        "ready_data_db",
        "ready_data_default_table",
        "load_behavior",
        "description",
    ]
    for key in dag_infos_necessary_keys:
        if key not in dag_infos:
            raise KeyError(f'Necessary key dag_infos["{key}"] is missing.')

    print("Validate config successfully.")


# Customized for each DAG
def _etl_func_missing():
    error_message = """
        Please implement the ETL function and add it to the DAG.
        If you are not sure what to do, please refer to `dag/template/template_dag.py`.
        There are some step or process is not necessary for common ETL, but necessary for City Dashboard,
            such as `wkb_geometry`, `dataset_info` and `lasttime_in_data` parts.
        
        A recommended ETL function should include the following steps:
        1. **Extract raw data from source**
            Should only extracts source data, and keeps it as raw as possible.
            _Some useful functions can be found in `utils/extract_stage.py`._
        2. Validate raw data (optional)
            _Some useful functions can be found in `utils/validate_stage.py`._
        3. Load raw data to PostgreSQL (optional)
            _Some useful functions can be found in `utils/load_stage.py`._
        4. **Transform raw data to ready data**
            All the data cleansing, data transformation, feature engineering should be done in this function.
            _Some useful functions can be found in `utils/transform_.*.py`._
        5. Validate ready data (optional)
            _Some useful functions can be found in `utils/validate_stage.py`._
        6. **Load ready data to PostgreSQL**
            _Some useful functions can be found in `utils/load_stage.py`._
        7. **Update lasttime_in_data to dataset_info table**
            Persist the lasttime_in_data for City Dashboard to use.
            _Some useful functions can be found in `utils/load_stage.py`._
    """
    raise RuntimeError(error_message)


def _create_or_update_dataset_info(psql_uri, config):
    """
    Create dataset_info table if not exists, or update if exists.
    """
    dag_infos = config["dag_infos"]
    data_infos = config["data_infos"]
    resource_updatetime = get_tpe_now_time()

    # Generate info that will be used to create or update dataset_info
    unique_column = "id"
    info = {
        "id": dag_infos.get("dag_id", None),
        "psql_table_name": dag_infos.get("ready_data_default_table", None),
        "name_cn": data_infos.get("name_cn", None),
        "airflow_dag_id": dag_infos.get("dag_id", None),
        "mongo_collection": None,
        "maintain_type": dag_infos.get("maintain_type", None),
        "airflow_update_freq": data_infos.get("airflow_update_freq", None),
        "source": data_infos.get("source", None),
        "source_type": data_infos.get("source_type", None),
        "source_department": data_infos.get("source_dept", None),
        # 'lasttime_in_data': update in etl_function
        # 'resource_updatetime': update individually,
        "gis_format": data_infos.get("gis_format", None),
        "coordinate": data_infos.get("coordinate", None),
        "is_geometry": data_infos.get("is_geometry", None),
        "dataset_description": data_infos.get("dataset_description", None),
        "etl_description": data_infos.get("etl_description", None),
        # 'been_used_count': auto trigger column
        "sensitivity": data_infos.get("sensitivity", None),
        # 'update_at': not use, the same as '_mtime'
        # 'create_at': not use
        # '_mtime': auto trigger column
        "schedule_interval": dag_infos.get("schedule_interval", None),
    }
    # if multiple table names, join with ','
    if isinstance(info["psql_table_name"], list):
        info["psql_table_name"] = ",".join(info["psql_table_name"])

    # Upsert to dataset_info
    # generate sql
    dataset_info_columns = ",".join(info.keys())
    dataset_info_values = ",".join([f"'{str(v)}'" for v in info.values()])
    dataset_info_update_pairs = ",".join(
        [f"{k}='{v}'" for k, v in info.items() if k != unique_column]
    )
    upsert_sql = f"""
        INSERT INTO dataset_info ({dataset_info_columns})
        VALUES ({dataset_info_values})
        ON CONFLICT ({unique_column})
        DO
        UPDATE SET {dataset_info_update_pairs}
    """
    update_resourece_updatetime_sql = f"""
        UPDATE dataset_info
        SET resource_updatetime = '{resource_updatetime}'
        WHERE {unique_column} = '{info['id']}'
    """
    # execute
    engine = create_engine(psql_uri)
    conn = engine.connect()
    conn.execute(sa_text(upsert_sql).execution_options(autocommit=True))
    conn.execute(
        sa_text(update_resourece_updatetime_sql).execution_options(autocommit=True)
    )
    conn.close()


class CommonDag:
    def __init__(self, proj_folder, dag_folder):
        self.data_path = DATA_PATH
        self.dag_path = os.path.join(DAG_PATH, proj_folder, dag_folder)
        self.config = _read_config(self.dag_path)
        _validate_config(self.config)

        self.proxies = PROXIES
        self.raw_data_db_uri = PostgresHook(
            postgres_conn_id=self.config["dag_infos"]["raw_data_db"]
        ).get_uri()
        self.ready_data_db_uri = PostgresHook(
            postgres_conn_id=self.config["dag_infos"]["ready_data_db"]
        ).get_uri()

    def fetch_email_list(self, mail_list: list):
        """
        For the convenience of using the email list, users are allowed to set up mail groups ending
        with 'EMAIL_LIST' in the Airflow variable. This way, there is no need to fill in each one
        in the DAG config; as long as the key matches, it will be automatically fetch from Airflow.
        """
        if len(mail_list) == 0:
            return None

        if isinstance(mail_list, str):
            mail_list = [mail_list]

        origin_mail_list = mail_list.copy()
        for mail in mail_list:
            # fetch email list from Airflow Variables
            if mail.endswith("MAIL_LIST"):
                variable_mail_list = Variable.get(mail, None)
                if variable_mail_list is None:
                    raise KeyError(f"Can not find the variable {mail} from Airflow.")
                origin_mail_list += literal_eval(Variable.get(mail))
                origin_mail_list.remove(mail)
        return list(set(origin_mail_list))

    def create_dag(self, etl_func=_etl_func_missing):
        dag_infos = self.config["dag_infos"]
        data_infos = self.config["data_infos"]
        default_args = dag_infos["default_args"]
        default_args["email"] = self.fetch_email_list(default_args.get("email", []))

        # Create Pipeline
        dag = DAG(
            dag_id=dag_infos["dag_id"],
            default_args=default_args,
            start_date=datetime.strptime(dag_infos["start_date"], "%Y-%m-%d"),
            schedule_interval=dag_infos["schedule_interval"],
            tags=dag_infos["tags"],
            catchup=dag_infos["catchup"],
            description=dag_infos["description"],
        )

        # Tasks
        with dag:
            get_and_validate_config = DummyOperator(task_id="get_job_config")

            etl = PythonOperator(
                task_id="etl",
                python_callable=etl_func,
                op_kwargs={
                    "dag_infos": dag_infos,
                    "raw_data_db_uri": self.raw_data_db_uri,
                    "ready_data_db_uri": self.ready_data_db_uri,
                    "proxies": self.proxies,
                    "data_path": self.data_path,
                },
            )

            update_dataset_info = PythonOperator(
                task_id="update_dataset_info",
                python_callable=_create_or_update_dataset_info,
                op_kwargs={"psql_uri": self.ready_data_db_uri, "config": self.config},
            )

            dag_execution_success = DummyOperator(task_id="dag_execution_success")

            # Pipeline
            get_and_validate_config >> etl >> update_dataset_info >> dag_execution_success
        return dag
