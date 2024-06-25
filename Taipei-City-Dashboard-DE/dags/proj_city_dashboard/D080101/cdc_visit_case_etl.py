from airflow import DAG


def cdc_visit_case_etl(url, diease_name, **kwargs):
    from datetime import datetime, timedelta

    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import download_file
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    def _year_week_to_date(years, weeks):
        last_day_of_weeks = []
        for year, week in zip(years, weeks):
            first_day_of_year = datetime(year, 1, 1)
            last_day_of_week = first_day_of_year + timedelta(days=int((week * 7) - 1))
            last_day_of_weeks.append(last_day_of_week)
        return last_day_of_weeks

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    file_name = f"{dag_id}.csv"
    REFERENCE_WINDOW_WEEK = 60
    VISIT_TYPE = "門診"
    COUNTY = "台北市"

    # Extract
    local_file = download_file(file_name, url, is_proxy=True, is_verify=False)
    raw_data = pd.read_csv(local_file)
    raw_data["data_time"] = _year_week_to_date(raw_data["年"], raw_data["週"])

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "年": "year",
            "週": "week",
            "就診類別": "visit_type",
            "年齡別": "age_group",
            "縣市": "county",
            f"{diease_name}健保就診人次": "patient_visit",
            "健保就診總人次": "total_nhi_patient_visit",
        }
    )
    # define columns type
    int_cols = ["year", "week", "patient_visit", "total_nhi_patient_visit"]
    for col in int_cols:
        data[col] = data[col].astype("int")
    # add disease type for other disease data join
    data["disease_type"] = diease_name
    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # filter data
    data = data.loc[(data["visit_type"] == VISIT_TYPE) & (data["county"] == COUNTY)]
    # aggregate data
    agg_data = (
        data.groupby(["data_time"])
        .agg(
            {
                "year": "first",
                "week": "first",
                "county": "first",
                "visit_type": "first",
                "patient_visit": "sum",
                "total_nhi_patient_visit": "sum",
            }
        )
        .reset_index()
    )
    # add support line
    agg_data = agg_data.sort_values(by=["data_time"])
    mean = agg_data["patient_visit"].iloc[-REFERENCE_WINDOW_WEEK:].mean()
    std = agg_data["patient_visit"].iloc[-REFERENCE_WINDOW_WEEK:].std()
    agg_data["visit_mean"] = mean
    agg_data["visit_std"] = std
    for i in range(1, 4):
        agg_data[f"visit_p{i}sd"] = (mean + (i * std)).round()
    # add warning status
    agg_data["status"] = "green"
    agg_data.loc[agg_data["patient_visit"] > agg_data["visit_p1sd"], "status"] = "yellow"
    agg_data.loc[agg_data["patient_visit"] > agg_data["visit_p2sd"], "status"] = "red"
    # select columns
    ready_data = agg_data[
        [
            "data_time",
            "year",
            "week",
            "visit_type",
            "county",
            "patient_visit",
            "total_nhi_patient_visit",
            "visit_mean",
            "visit_std",
            "visit_p1sd",
            "visit_p2sd",
            "visit_p3sd",
            "status",
        ]
    ]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)
