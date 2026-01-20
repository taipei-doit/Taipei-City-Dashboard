from operators.common_pipeline import CommonDag
from airflow.models import Variable

from utils.housekeeping import housekeep_tables


def _transfer(**kwargs):
    raw_value = Variable.get("HOUSEKEEPING_TABLES", default_var="[]")
    if not raw_value:
        return 0

    table_names = raw_value
    if isinstance(raw_value, str):
        try:
            import json

            table_names = json.loads(raw_value)
        except Exception:
            from ast import literal_eval

            table_names = literal_eval(raw_value)

    if not table_names:
        return 0

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    if not ready_data_db_uri:
        raise ValueError("Missing ready_data_db_uri in kwargs (expected from CommonDag)")

    return housekeep_tables(
        table_names=table_names,
        ready_data_db_uri=ready_data_db_uri,
        dag_infos=kwargs.get("dag_infos"),
    )


dag = CommonDag(proj_folder="common_dags", dag_folder="housekeeping_tables")
dag.create_dag(etl_func=_transfer)
