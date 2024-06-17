from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0017(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_file_last_modified_time
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_address import (
        clean_data,
        get_addr_xy_parallel,
        main_process,
        save_data,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=9def0ac0-ad65-4f34-a8a6-aeba704c70d4"
    PAGE_ID = "aaf97773-3631-40e2-b3cc-da87bf2ce1d5"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Polygon"

    # Extract
    raw_data = pd.read_excel(URL)
    raw_data["update_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "聯絡人連絡電話": "聯絡人電話",
            "管理人連絡電話": "管理人電話",
            "容納人數(人)": "容納人數",
            "收容所編號": "編碼",
            "門牌": "道路門牌",
        }
    )
    # Time
    data["update_time"] = convert_str_to_time_format(data["update_time"])
    # Convert data type of the column "容納人數"
    if data["容納人數"].dtype != "int64":
        data["容納人數"] = data["容納人數"].apply(
            lambda x: "".join(x.split(",")) if isinstance(x, str) else "0"
        )
        data["容納人數"] = pd.to_numeric(data["容納人數"], downcast="integer")
    # Fill the change field with a None value
    if "備考" not in data.columns:
        data["備考"] = None
    data = data.reindex(
        columns=[
            "名稱",
            "縣市",
            "鄉鎮",
            "村里",
            "道路門牌",
            "水災",
            "震災",
            "土石流",
            "海嘯",
            "是否設置無障礙設施",
            "室內",
            "室外",
            "服務里別",
            "容納人數",
            "聯絡人姓名",
            "聯絡人電話",
            "管理人姓名",
            "管理人電話",
            "備考",
            "編碼",
            "wkb_geometry",
            "update_time",
        ],
        fill_value="None",
    )
    # clean addr
    data["address"] = data["縣市"] + data["鄉鎮"] + data["村里"] + data["道路門牌"]
    addr = data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    data["address"] = output
    # geocoding
    x, y = get_addr_xy_parallel(output)
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(data, x, y, from_crs=FROM_CRS)
    # select columns
    ready_data = gdata[
        [
            "名稱",
            "縣市",
            "鄉鎮",
            "村里",
            "道路門牌",
            "水災",
            "震災",
            "土石流",
            "海嘯",
            "是否設置無障礙設施",
            "室內",
            "室外",
            "服務里別",
            "容納人數",
            "聯絡人姓名",
            "聯絡人電話",
            "管理人姓名",
            "管理人電話",
            "備考",
            "編碼",
            "wkb_geometry",
            "update_time",
        ]
    ]

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["update_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0017")
dag.create_dag(etl_func=_R0017)
