from airflow import DAG
from operators.common_pipeline import CommonDag


SPORTS_CENTER_URL = "https://data.taipei/api/dataset/80be7612-593f-4795-9935-a10ce0f7b75b/resource/e7c46724-3517-4ce5-844f-5a4404897b7d/download"
REALTIME_URL = "https://booking-tpsc.sporetrofit.com/Home/loadLocationPeopleNum"


def _transfer(**kwargs):
    import io

    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    center_response = requests.get(SPORTS_CENTER_URL, proxies=proxies, timeout=60)
    center_response.raise_for_status()
    raw_centers = pd.read_csv(io.BytesIO(center_response.content))
    if raw_centers.empty:
        raise ValueError("Data Taipei sports center CSV returned no records.")

    centers = raw_centers.rename(
        columns={
            "名稱": "name",
            "郵遞區號": "postal_code",
            "地址": "address",
            "電話": "phone",
            "網址": "website",
            "經度": "lng",
            "緯度": "lat",
        }
    )
    centers["data_time"] = get_tpe_now_time_str()
    centers["lng"] = pd.to_numeric(centers["lng"], errors="coerce")
    centers["lat"] = pd.to_numeric(centers["lat"], errors="coerce")
    centers["postal_code"] = centers["postal_code"].astype(str).str.strip()

    people_response = requests.post(
        REALTIME_URL,
        headers={
            "accept": "*/*",
            "content-length": "0",
            "origin": "https://booking-tpsc.sporetrofit.com",
            "referer": "https://booking-tpsc.sporetrofit.com/Home/LocationPeopleNum",
            "x-requested-with": "XMLHttpRequest",
            "user-agent": "Mozilla/5.0",
        },
        proxies=proxies,
        timeout=60,
    )
    people_response.raise_for_status()
    people_payload = people_response.json()
    people = pd.DataFrame(people_payload.get("locationPeopleNums", []))

    if people.empty:
        people = pd.DataFrame(columns=["LID", "lidName"])
    people = people.rename(
        columns={
            "LID": "location_id",
            "lidName": "realtime_name",
            "swPeopleNum": "sw_people_num",
            "swMaxPeopleNum": "sw_max_people_num",
            "gymPeopleNum": "gym_people_num",
            "gymMaxPeopleNum": "gym_max_people_num",
        }
    )
    people["join_name"] = people["realtime_name"].astype(str).str.strip()
    for column in [
        "sw_people_num",
        "sw_max_people_num",
        "gym_people_num",
        "gym_max_people_num",
    ]:
        if column not in people.columns:
            people[column] = pd.NA
        people[column] = pd.to_numeric(people[column], errors="coerce")

    centers["join_name"] = centers["name"].str.replace("運動中心.*", "", regex=True)
    data = centers.merge(
        people[
            [
                "join_name",
                "location_id",
                "realtime_name",
                "sw_people_num",
                "sw_max_people_num",
                "gym_people_num",
                "gym_max_people_num",
            ]
        ],
        on="join_name",
        how="left",
    )
    data["sw_usage_rate"] = data["sw_people_num"] / data["sw_max_people_num"]
    data["gym_usage_rate"] = data["gym_people_num"] / data["gym_max_people_num"]
    data = data.dropna(subset=["lng", "lat"]).copy()

    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=4326
    )
    ready_data = gdata[
        [
            "data_time",
            "name",
            "postal_code",
            "address",
            "phone",
            "website",
            "location_id",
            "realtime_name",
            "sw_people_num",
            "sw_max_people_num",
            "sw_usage_rate",
            "gym_people_num",
            "gym_max_people_num",
            "gym_usage_rate",
            "lng",
            "lat",
            "wkb_geometry",
        ]
    ]

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point",
    )

    update_lasttime_in_data_to_dataset_info(
        engine,
        airflow_dag_id=dag_id,
        lasttime_in_data=ready_data["data_time"].max(),
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="sports_center")
dag.create_dag(etl_func=_transfer)
