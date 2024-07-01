from airflow import DAG
from operators.common_pipeline import CommonDag


def _D060103(**kwargs):
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.extract_stage import get_shp_file
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    def get_datataipei_file_url(page_id):
        url = f"https://data.taipei/api/frontstage/tpeod/dataset.view?id={page_id}"
        res = requests.get(url)
        res.raise_for_status()
        res_json = res.json()
        data_list = res_json["payload"]["resources"]
        url_list = {}
        for data in data_list:
            if data["file_format"] != "ZIP":
                continue
            file_tag = data["name"].replace("臺北市", "").replace("圖資資料", "")
            url = "https://data.taipei" + data["url"]
            last_modified = data["last_modified"]
            url_list[file_tag] = (url, last_modified)
        return url_list

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    PAGE_ID = "cabdf272-e0ec-4e4e-9136-f4b8596f35d9"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    # get all data url
    data_list = get_datataipei_file_url(PAGE_ID)
    # get data
    raw_datas = []
    for file_tag, (url, last_modified) in data_list.items():
        file_name = dag_id + file_tag
        raw_data = get_shp_file(url, file_name, FROM_CRS)
        raw_data["file_tag"] = file_tag
        raw_data["data_time"] = last_modified
        raw_datas.append(raw_data)

    # Transform
    ready_datas = []
    for raw_data in raw_datas:
        data = raw_data.copy()
        # rename
        data = data.rename(
            columns={
                "file_tag": "file_tag",
                "OBJECTID": "seq",  # 流水ID
                "SITEM_NO": "attr",  # 人民團體-分類
                "code": "code",
                "number": "code",  # 人民團體-代碼編號
                "name": "name",
                "type": "type",
                "multitype": "type",  # 社福據點_福利健康地圖-類型
                "teamYN": "type",  # 托嬰中心-類型
                "service": "attr",  # 老人照護機構_衛生局-服務類型
                "attr": "attr",  # 身障設施-屬性類別
                "zipcode": "zipcode",
                "town": "town",
                "address": "address",
                "location": "address",  # 身障友善環境-所在地點
                "note": "note",  # 身障友善環境-備註
                "tel": "tel",
                "fax": "fax",
                "lon": "lng",
                "lat": "lat",
                "x": "lng_twd97",
                "y": "lat_twd97",
                "publicYN": "public_type",  # 公私立
                "is_accessi": "is_accessible",  # 身障設施-unknown
                "data_time": "data_time",
            }
        )
        if data["file_tag"].iloc[0] == "老人照護機構-衛生局":
            data = data.rename(columns={"type": "is_public", "attr": "type"})
        if data["file_tag"].iloc[0] == "老人照護機構":
            data = data.rename(columns={"type": "is_public"})
        # standardize time
        data["data_time"] = convert_str_to_time_format(data["data_time"])
        # if lng and lat equal to 0, replace with None
        data["lng"] = data["lng"].replace(0, None)
        data["lat"] = data["lat"].replace(0, None)
        # standardize geometry
        gdata = add_point_wkbgeometry_column_to_df(
            data, data["lng"], data["lat"], from_crs=FROM_CRS
        )
        # select columns
        # because not every data has full columns, fill None to the missing columns
        select_cols = [
            "data_time",
            "file_tag",
            "seq",
            "code",
            "name",
            "type",
            "attr",
            "zipcode",
            "town",
            "address",
            "tel",
            "lng",
            "lat",
            "wkb_geometry",
        ]
        for col in select_cols:
            if col not in list(gdata.columns):
                gdata[col] = None
        ready_data = gdata[select_cols]
        ready_datas.append(ready_data)

    # Load
    engine = create_engine(ready_data_db_uri)
    for ready_data in ready_datas:
        save_geodataframe_to_postgresql(
            engine,
            gdata=ready_data,
            load_behavior=load_behavior,
            default_table=default_table,
            history_table=history_table,
            geometry_type=GEOMETRY_TYPE,
        )
        update_lasttime_in_data_to_dataset_info(
            engine, dag_id, data["data_time"].max()
        )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D060103")
dag.create_dag(etl_func=_D060103)
