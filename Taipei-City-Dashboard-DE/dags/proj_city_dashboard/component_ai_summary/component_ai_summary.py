from airflow import DAG
from operators.common_pipeline import CommonDag
from proj_city_dashboard.component_ai_summary.ai_summary_etl import ai_summary_etl


def component_ai_summary(**kwargs):
    ai_summary_etl(**kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="component_ai_summary")
dag.create_dag(etl_func=component_ai_summary)
