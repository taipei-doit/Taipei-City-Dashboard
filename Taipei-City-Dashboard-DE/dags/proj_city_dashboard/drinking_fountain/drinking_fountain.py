from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    url = "https://data.taipei/api/v1/dataset/181097e0-c171-4bcd-ad41-c7b55dbc616e"
    limit = 1000
    offset = 0
    records = []

    while True:
        response = requests.get(
            url,
            params={
                "scope": "resourceAquire",
                "limit": limit,
                "offset": offset,
            },
            proxies=proxies,
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()["result"]
        records.extend(payload.get("results", []))
        offset += limit
        if offset >= payload.get("count", 0):
            break

    raw_data = pd.DataFrame(records)
    if raw_data.empty:
        raise ValueError("Data Taipei drinking fountain API returned no records.")

    data = raw_data.rename(
        columns={
            "_id": "source_id",
            "直飲臺編號": "fountain_id",
            "轄區分處": "branch",
            "市別": "city",
            "場所別": "place_type",
            "場所次分類": "place_subtype",
            "所屬單位": "owner_unit",
            "場所名稱": "place_name",
            "地址": "address",
            "行政區": "district",
            "維護單位": "maintenance_unit",
            "連絡電話": "phone",
            "場所開放時間": "open_time",
            "設置地點": "install_location",
            "經度": "lng",
            "緯度": "lat",
            "狀態": "status",
            "狀態異動日期時間": "status_updated_at",
            "最近採樣日期時間": "latest_sampled_at",
            "大腸桿菌數": "e_coli_count",
            "水質及維護資訊網址": "quality_info_url",
            "直飲台照片網址": "photo_url",
        }
    )

    data["data_time"] = get_tpe_now_time_str()
    data["lng"] = pd.to_numeric(data["lng"], errors="coerce")
    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    data["status_updated_at"] = convert_str_to_time_format(
        data["status_updated_at"], from_format="%Y%m%dT%H%M%S", errors="coerce"
    )
    data["latest_sampled_at"] = convert_str_to_time_format(
        data["latest_sampled_at"], from_format="%Y%m%dT%H%M%S", errors="coerce"
    )
    data = data.dropna(subset=["lng", "lat"]).copy()

    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=4326
    )
    ready_data = gdata[
        [
            "data_time",
            "source_id",
            "fountain_id",
            "branch",
            "city",
            "place_type",
            "place_subtype",
            "owner_unit",
            "place_name",
            "address",
            "district",
            "maintenance_unit",
            "phone",
            "open_time",
            "install_location",
            "lng",
            "lat",
            "status",
            "status_updated_at",
            "latest_sampled_at",
            "e_coli_count",
            "quality_info_url",
            "photo_url",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="drinking_fountain")
dag.create_dag(etl_func=_transfer)
