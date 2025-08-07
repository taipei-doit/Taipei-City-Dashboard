from airflow import DAG
from operators.common_pipeline import CommonDag
from sqlalchemy import create_engine
from airflow.models import Variable
import logging


MAPPINGS = Variable.get("SPATIAL_MAPPINGS", deserialize_json=True)

def build_update_sql(cfg: dict) -> str:
    if cfg["src_table"].endswith("_ntpe"):
        tgt_table, tgt_name, extra = "public.tw_village", "town_name", "AND county_name = '新北市'"
    else:
        tgt_table, tgt_name, extra = "public.tp_district", "tname", ""
    return f"""
    UPDATE {cfg['src_table']} AS s
    SET {cfg['src_area_col']} = t.{tgt_name}
    FROM {tgt_table} AS t
    WHERE ST_Within(s.wkb_geometry, t.wkb_geometry)
      {extra}
      AND s.{cfg['src_area_col']} IS DISTINCT FROM t.{tgt_name};
    """

def _transfer(**kwargs):
    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    engine = create_engine(ready_data_db_uri)
    # main
    results = []
    conn = engine.connect()
    with engine.begin() as conn:
        for cfg in MAPPINGS:
            sql = build_update_sql(cfg)
            result = conn.execute(text(sql))
            updated = result.rowcount
            logging.info("Mapping %-40s → updated %4d rows", cfg["src_table"], updated)
            results.append({"table": cfg["src_table"], "updated": updated})


dag = CommonDag(proj_folder="common_dags", dag_folder="spatial_area_mapping")
dag.create_dag(etl_func=_transfer)
