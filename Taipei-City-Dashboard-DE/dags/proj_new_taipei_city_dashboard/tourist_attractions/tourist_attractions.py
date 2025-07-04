from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import NewTaipeiAPIClient
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID= "b3a30a19-4b89-4da2-8d99-18200dc5dfde"
    GEOMETRY_TYPE = "Point"
    client = NewTaipeiAPIClient(RID, input_format="json")
    res = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(res)
    data = raw_data.copy()
    
    # 資料格式為"108臺北市萬華區昆明街142號7-8樓", 只取區
    data['distric'] = data['Add'].str.findall(r'[\u4e00-\u9fa5]+區').str[-1]

    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["Px"], y=data["Py"], from_crs=4326
    )
        # select column
    gdata = gdata.rename(
        columns={
            "Px": "longitude",
            "Py": "latitude",
            "Add": "address",
            "Description": "introduction",
            "Tel": "tel",
            "Name": "name",
        }
    )
    # 資料來源:交通部觀光資訊標準格式 v1.0
    # 建立分類代碼對應表
    category_mapping = {
        '01': '文化類',
        '02': '生態類', 
        '03': '古蹟類',
        '04': '廟宇類',
        '05': '藝術類',
        '06': '小吃/特產類',
        '07': '國家公園類',
        '08': '國家風景區類',
        '09': '休閒農業類',
        '10': '溫泉類',
        '11': '自然風景類',
        '12': '遊憩類',
        '13': '體育健身類',
        '14': '觀光工廠類',
        '15': '都會公園類',
        '16': '森林遊樂區類',
        '17': '林場類',
        '18': '其他'
    }

    # 將數字代碼轉換為分類名稱
    gdata["type"] = gdata["Class1"].astype(str).str.zfill(2).map(category_mapping).fillna('其他')
    gdata["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    data = gdata[["name", "type", "introduction", "address", "distric", "tel", "longitude", "latitude","data_time", "wkb_geometry"]]
    # 重新排列欄位順序

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, data["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="tourist_attractions")
dag.create_dag(etl_func=_transfer)
