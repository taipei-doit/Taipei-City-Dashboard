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
    url = "https://statistics.health.gov.tw/tbl/m005%E6%B3%95%E5%AE%9A%E5%82%B3%E6%9F%93%E7%97%85%E7%A2%BA%E5%AE%9A%E7%97%85%E4%BE%8B(%E8%A1%8C%E6%94%BF%E5%8D%80).html"
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

    df = pd.DataFrame(
        {
            "disease": flat[0],
            "district": flat[1],
            "year_month": flat[2],
            "case_count": flat[3],
        }
    )

    # Transform
    # Filter food-related diseases
    food_keywords = [
        "傷寒", "副傷寒", "A型肝炎", "桿菌性痢疾",
        "腸道出血性大腸桿菌", "阿米巴性痢疾", "霍亂",
        "李斯特菌症", "肉毒桿菌中毒",
    ]
    df = df[df["disease"].apply(lambda x: any(k in x for k in food_keywords))]
    # Exclude typhus diseases (斑疹傷寒) which are vector-borne, not food-borne
    df = df[~df["disease"].str.contains("斑疹傷寒", na=False)]

    # Remove '其他' district
    df = df[df["district"] != "其他"]

    # Parse ROC year-month to Gregorian timestamp
    def parse_roc_year_month(ym):
        m = re.match(r"(\d+)年(\d+)月", ym)
        if not m:
            return None
        roc_year = int(m.group(1))
        month = int(m.group(2))
        gregorian_year = roc_year + 1911
        return pd.Timestamp(f"{gregorian_year}-{month:02d}-01", tz="Asia/Taipei")

    df["data_time"] = df["year_month"].apply(parse_roc_year_month)
    df = df.dropna(subset=["data_time"])

    # Clean disease name for display
    df["disease_name"] = df["disease"].apply(
        lambda x: x.split("/")[-1] if "/" in x else x
    )

    # Aggregate by month and disease (sum across all districts)
    agg = (
        df.groupby(["data_time", "disease_name"])
        .agg({"case_count": "sum"})
        .reset_index()
    )

    # Ensure numeric
    agg["case_count"] = pd.to_numeric(agg["case_count"], errors="coerce").fillna(0).astype(int)

    # Add year and month columns for convenience
    agg["year"] = agg["data_time"].dt.year
    agg["month"] = agg["data_time"].dt.month

    ready_data = agg[["data_time", "year", "month", "disease_name", "case_count"]]

    # District-level aggregation (sum all food-related diseases per district per month)
    district_agg = (
        df.groupby(["data_time", "district"])
        .agg({"case_count": "sum"})
        .reset_index()
    )
    district_agg["case_count"] = pd.to_numeric(district_agg["case_count"], errors="coerce").fillna(0).astype(int)
    district_agg["year"] = district_agg["data_time"].dt.year
    district_agg["month"] = district_agg["data_time"].dt.month
    district_data = district_agg[["data_time", "year", "month", "district", "case_count"]]
    district_data = district_data.rename(columns={"case_count": "total_case_count"})

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    save_dataframe_to_postgresql(
        engine,
        data=district_data,
        load_behavior=load_behavior,
        default_table="infectious_food_disease_district_monthly",
        history_table="infectious_food_disease_district_monthly_history",
    )
    update_lasttime_in_data_to_dataset_info(
        engine, dag_id, ready_data["data_time"].max()
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="infectious_food_disease_monthly")
dag.create_dag(etl_func=_transfer)
