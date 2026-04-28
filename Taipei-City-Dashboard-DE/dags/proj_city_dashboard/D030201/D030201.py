from airflow import DAG
from operators.common_pipeline import CommonDag


def _D030201(**kwargs):
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    def get_datataipei_file_rid(page_id):
        url = f"https://data.taipei/api/frontstage/tpeod/dataset.view?id={page_id}"
        res = requests.get(url)
        res.raise_for_status()
        res_json = res.json()
        data_list = res_json["payload"]["resources"]
        url_list = {}
        for data in data_list:
            file_tag = data["name"].split("年")[0]
            rid = data["rid"]
            url_list[file_tag] = rid
        return url_list

    def get_existing_data(ready_data_db_uri, table_name, column='file_tag'):
        engine = create_engine(ready_data_db_uri)
        sql = f"select distinct {column} from {table_name}"
        existing_tag = pd.read_sql(sql, engine).iloc[:, 0]
        return existing_tag.tolist()

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    PAGE_ID = "2f238b4f-1b27-4085-93e9-d684ef0e2735"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    # get all data url
    data_list = get_datataipei_file_rid(PAGE_ID)
    # filter out existing year
    existing_year = get_existing_data(ready_data_db_uri, default_table)
    new_data_list = {k: v for k, v in data_list.items() if k not in existing_year}
    # get data
    raw_datas = []
    for file_tag, rid in new_data_list.items():
        raw_data = get_data_taipei_api(rid, output_format="dataframe")
        raw_data["file_tag"] = file_tag
        raw_datas.append(raw_data)

    # Transform
    ready_datas = []
    for raw_data in raw_datas:
        data = raw_data.copy()
        # rename
        # truncate the digit in front of columns name
        data.columns = data.columns.str.replace(r"^\d+", "", regex=True)
        data = data.rename(
            columns={
                "file_tag": "file_tag",
                "發生年度": "year",
                "發生月": "month",
                "發生日": "day",
                "發生時－hours": "hour",
                "發生分": "minute",
                "處理別－編號": "case_type",
                "區序": "town",
                "肇事地點": "address",
                "死亡人數": "death_person",
                "受傷人數": "injury_person",
                "當事人序號": "person_seq",
                "車種": "car_type",
                "性別": "gender",
                "年齡": "age",
                "受傷程度": "injury_level",
                "座標－x": "lng",
                "座標－y": "lat",
                # it used to be "2－30日死亡人數" before data.columns.str.replace(r"^\d+", "", regex=True)
                "－30日死亡人數": "death_2_30_days",
                "天候": "weather",
                "光線": "light",
                "道路類別": "road_category",
                "速限－速度限制": "speed_limit",
                "道路型態": "road_type",
                "事故位置": "accident_location",
                "路面狀況1": "road_condition1",
                "路面狀況2": "road_condition2",
                "路面狀況3": "road_condition3",
                "道路障礙1": "road_obstacle1",
                "道路障礙2": "road_obstacle2",
                "號誌1": "signal1",
                "號誌2": "signal2",
                "車道劃分－分向": "lane_direction",
                "車道劃分－分道1": "lane_division1",
                "車道劃分－分道2": "lane_division2",
                "車道劃分－分道3": "lane_division3",
                "事故類型及型態": "accident_type",
                "主要傷處": "main_injury",
                "保護裝置": "protective_device",
                "行動電話": "cellphone",
                "車輛用途": "vehicle_purpose",
                "當事者行動狀態": "person_status",
                "駕駛資格情形": "driver_license",
                "駕駛執照種類": "driver_license_type",
                "飲酒情形": "drinking",
                "車輛撞擊部位1": "vehicle_impact1",
                "車輛撞擊部位2": "vehicle_impact2",
                "肇因碼－個別": "cause_code_individual",
                "肇因碼－主要": "cause_code_main",
                "個人肇逃否": "hit_and_run",
                "職業": "occupation",
                "旅次目的": "trip_purpose",
                "安全帽": "helmet",
                "data_time": "data_time",
            }
        )
        # the mapping code can be found in 道路交通事故調查報告表
        # https://drive.motc.gov.tw/public.php?service=files&t=n-_kmDDqYgEitECs70aS9chdDgZlINuGzqyUd9G433mI0PQA-tTPqDSCMJcy1zLd
        # define columns  ype
        str_cols = [
            "town",
            "address",
            "car_type",
            "file_tag",
            "data_time",
            "year",
            "month",
            "day",
            "hour",
            "minute",
        ]
        for col in str_cols:
            data[col] = data[col].astype(str).str.strip()
        num_cols = list(set(data.columns) - set(str_cols) - set(["_id", "_importdate"]))
        for col in num_cols:
            data[col] = pd.to_numeric(data[col], errors="coerce")
        # delete any digit in  town
        data["town"] = data["town"].str.replace("\\d+", "", regex=True)
        # standardize time
        data["data_time"] = convert_str_to_time_format(data["data_time"])
        occurred_time = (
            data["year"].str.zfill(3)
            + "-"
            + data["month"].str.zfill(2)
            + "-"
            + data["day"].str.zfill(2)
            + " "
            + data["hour"].str.zfill(2)
            + ":"
            + data["minute"].str.zfill(2)
        )
        data["occurred_time"] = convert_str_to_time_format(
            occurred_time, from_format="%TY-%m-%d %H:%M"
        )
        data["epoch_time"] = data["occurred_time"].apply(lambda x: x.timestamp())
        # old data does not have lng and lat
        if list(data.columns) not in ["lng", "lat"]:
            data["lng"] = None
            data["lat"] = None
        # standardize geometry
        gdata = add_point_wkbgeometry_column_to_df(
            data, data["lng"], data["lat"], from_crs=FROM_CRS
        )
        # select columns
        # because not every year data has full columns, use drop to select columns
        ready_data = gdata.drop(
            columns=[
                "_id",
                "_importdate",
                "year",
                "month",
                "day",
                "hour",
                "minute",
                "geometry",
            ]
        )
        ready_datas.append(ready_data)

    # Load
    engine = create_engine(ready_data_db_uri)
    for ready_data in ready_datas:
        save_geodataframe_to_postgresql(
            engine,
            gdata=ready_data,
            load_behavior=load_behavior,
            default_table=default_table,
            geometry_type=GEOMETRY_TYPE,
        )
        update_lasttime_in_data_to_dataset_info(
            engine, dag_id, data["occurred_time"].max()
        )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D030201")
dag.create_dag(etl_func=_D030201)
