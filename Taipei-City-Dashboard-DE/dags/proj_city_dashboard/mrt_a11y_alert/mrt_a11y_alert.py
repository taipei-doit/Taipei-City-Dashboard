from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        get_current_rid_from_page_id,
        get_data_taipei_api,
    )
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    PAGE_ID = "d884a9c6-f86c-4854-8da7-e6516ddbe612"

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    rid = get_current_rid_from_page_id(PAGE_ID)
    raw_list = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(raw_list)
    if raw_data.empty:
        ready_data = pd.DataFrame(
            columns=["line", "station", "publish_time", "description", "status", "data_time"]
        )
    else:
        raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]
        data = raw_data.rename(
            columns={
                "路線": "line",
                "車站": "station",
                "日期時間": "publish_time",
                "說明": "description",
            }
        )
        # 統一 station 命名：去掉「站」字尾，與 elevator 表 regex parse 結果對齊
        data["station"] = data["station"].str.replace(r"站$", "", regex=True)
        # publish_time 來源格式 "20260420T213100"（ISO8601 無分隔）
        data["publish_time"] = convert_str_to_time_format(
            data["publish_time"], from_format="%Y%m%dT%H%M%S"
        )
        # status 從說明文字 parse：keyword 命中視為 closed，否則 active
        CLOSED_PATTERNS = r"(已修復|修復完成|已恢復|恢復正常|修復後|正常營運)"
        data["status"] = (
            data["description"]
            .str.contains(CLOSED_PATTERNS, na=False, regex=True)
            .map({True: "closed", False: "active"})
        )
        data["data_time"] = convert_str_to_time_format(data["data_time"])
        ready_data = data[
            ["line", "station", "publish_time", "description", "status", "data_time"]
        ]

    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    if not ready_data.empty:
        update_lasttime_in_data_to_dataset_info(
            engine, dag_id, ready_data["data_time"].max()
        )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="mrt_a11y_alert")
dag.create_dag(etl_func=_transfer)
