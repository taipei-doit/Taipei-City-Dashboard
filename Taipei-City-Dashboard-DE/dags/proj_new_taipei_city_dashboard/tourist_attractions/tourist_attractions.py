from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_tdx_data
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    # Load
    GEOMETRY_TYPE = "Point"
    TPE_URL = "https://tdx.transportdata.tw/api/basic/v2/Tourism/ScenicSpot/NewTaipei?%24format=JSON"
    res = get_tdx_data(TPE_URL, output_format='dataframe')
    df = res.copy()
    df["longitude"] = df["Position"].apply(lambda pos: pos.get("PositionLon") if isinstance(pos, dict) else None)
    df["latitude"] = df["Position"].apply(lambda pos: pos.get("PositionLat") if isinstance(pos, dict) else None)
    # zip code 對應區
    zipcode_to_area = {
    "207": "萬里區",
    "208": "金山區",
    "220": "板橋區",
    "221": "汐止區",
    "222": "深坑區",
    "223": "石碇區",
    "224": "瑞芳區",
    "226": "平溪區",
    "227": "雙溪區",
    "228": "貢寮區",
    "231": "新店區",
    "232": "坪林區",
    "233": "烏來區",
    "234": "永和區",
    "235": "中和區",
    "236": "土城區",
    "237": "三峽區",
    "238": "樹林區",
    "239": "鶯歌區",
    "241": "三重區",
    "242": "新莊區",
    "243": "泰山區",
    "244": "林口區",
    "247": "蘆洲區",
    "248": "五股區",
    "249": "八里區",
    "251": "淡水區",
    "252": "三芝區",
    "253": "石門區"
    }   

    df['distric'] = df['ZipCode'].astype(str).map(zipcode_to_area)


    df = df.rename(columns={
        "ScenicSpotName": "name",
        "DescriptionDetail": "introduction",
        "Phone": "tel",
        "Class1": "type",
        "City": "city"
    })

    gdata = add_point_wkbgeometry_column_to_df(
            df, x=df["longitude"], y=df["latitude"], from_crs=4326
        )

    df = gdata[["name", "type", "introduction", "city", "distric", "tel", "longitude", "latitude", "wkb_geometry"]]
    df["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=df,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, df["data_time"].max()
        )
    
dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="tourist_attractions")
dag.create_dag(etl_func=_transfer)
