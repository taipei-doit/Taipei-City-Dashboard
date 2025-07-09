from airflow import DAG
from operators.common_pipeline import CommonDag
import pandas as pd

def convert_vaccine_symbols(value):
    """Convert vaccine availability symbols to binary values"""
    if pd.isna(value) or value == '':
        return 0
    elif value == '◎':
        return 1
    elif '◎' in str(value):  # Handle cases like "◎\n限院內腎友及家屬"
        return 1
    else:
        return 0


def _transfer(**kwargs):
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str
    from utils.extract_stage import (
        get_data_taipei_file_last_modified_time,
        get_data_taipei_api,
    )
    from utils.transform_address import (
        clean_data,
        get_addr_xy_parallel,
        main_process,
        save_data,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    RID = "47b02c29-efa2-4614-ac7e-1b0b9499e6ea"
    PAGE_ID = "ec201f0a-2efa-4426-9439-a8daea7b33c7"
    # Extract
    res = get_data_taipei_api(RID)

    raw_data = pd.DataFrame(res)

    # Transform
    # Rename
    data = raw_data.copy()
    data = data.drop(columns=["_id", "_importdate"])
    

    data = data.rename(columns={
        "院所名稱": "name",
        "幼兒流感3歲以下": "flu_u3_child",
        "幼兒流感3歲以上": "flu_o3_child",
        "成人流感": "flu_adult",
        "地址": "address",
        "電話": "tel",
    })
    area_candidates = data['address'].str.slice(3, 6)
    data['district'] = area_candidates.apply(lambda x: x if x.endswith('區') else None)

    cols = ["flu_u3_child", "flu_o3_child", "flu_adult"]
    for col in cols:
        data[col] = data[col].apply(convert_vaccine_symbols)
        
    # 先根據疫苗三欄判斷要不要保留
    mask = (data["flu_u3_child"] == 1) | (data["flu_o3_child"] == 1) | (data["flu_adult"] == 1)

    df_filtered = data.loc[mask].copy()


    addr = df_filtered["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    df_filtered["address"] = output
    # get gis xy
    df_filtered["lon"], df_filtered["lat"] = get_addr_xy_parallel(output)
    # standardize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        df_filtered, x=df_filtered["lon"], y=df_filtered["lat"], from_crs=4326
    )

    df = gdata[["name", "tel", "address", "type", "lon", "lat", "district"]]
    df["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=df,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="POINT",
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, df["data_time"].max()
        )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="flu_hospitals_tpe")
dag.create_dag(etl_func=_transfer)
