from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import json
    import re

    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # Extract
    url = "https://statistics.health.gov.tw/tbl/b111%E9%A3%9F%E5%93%81%E4%B8%AD%E6%AF%92%E4%BA%8B%E4%BB%B6(%E5%A0%B4%E6%89%80%E5%88%A5).html"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    resp.encoding = "utf-8"

    match = re.search(
        r'<script type="application/json" data-for="[^"]+">(.+?)</script>',
        resp.text,
        re.DOTALL,
    )
    if not match:
        raise ValueError("Could not find embedded JSON data in the HTML page.")

    widget_data = json.loads(match.group(1))
    flat = widget_data["x"]["data"]

    # The data is 4 parallel arrays:
    # flat[0] = metric type (件數, 患者數, 死亡數)
    # flat[1] = venue type (總計, 自宅, 供膳之營業場所, ...)
    # flat[2] = year in ROC (91年, 92年, ...)
    # flat[3] = numeric value
    df = pd.DataFrame(
        {
            "metric_type": flat[0],
            "venue_type": flat[1],
            "year_roc": flat[2],
            "value": flat[3],
        }
    )

    # Transform
    # Convert ROC year to Gregorian
    df["year"] = df["year_roc"].str.replace("年", "", regex=False).astype(int) + 1911

    # Pivot metrics into columns
    pivot = df.pivot_table(
        index=["year", "venue_type"],
        columns="metric_type",
        values="value",
        aggfunc="first",
    ).reset_index()

    pivot = pivot.rename(
        columns={
            "件數": "incident_count",
            "患者數": "affected_people_count",
            "死亡數": "death_count",
        }
    )

    # Ensure all expected columns exist
    for col in ["incident_count", "affected_people_count", "death_count"]:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot["incident_count"] = pd.to_numeric(pivot["incident_count"], errors="coerce").fillna(0).astype(int)
    pivot["affected_people_count"] = pd.to_numeric(pivot["affected_people_count"], errors="coerce").fillna(0).astype(int)
    pivot["death_count"] = pd.to_numeric(pivot["death_count"], errors="coerce").fillna(0).astype(int)

    pivot["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    ready_data = pivot[[
        "year",
        "venue_type",
        "incident_count",
        "affected_people_count",
        "death_count",
        "data_time",
    ]]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(
        engine, dag_id, ready_data["data_time"].max()
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="food_poisoning_trend")
dag.create_dag(etl_func=_transfer)
