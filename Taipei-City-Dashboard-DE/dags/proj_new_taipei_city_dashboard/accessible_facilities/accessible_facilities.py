from airflow import DAG
from operators.common_pipeline import CommonDag

# pending 資料來源不全
def _transfer(**kwargs):
    return
    # import pandas as pd
    # from sqlalchemy import create_engine
    # from utils.extract_stage import TaipeiTravelAPIClient
    # from utils.load_stage import (
    #     save_dataframe_to_postgresql,
    #     update_lasttime_in_data_to_dataset_info,
    # )
    # from utils.transform_geometry import add_point_wkbgeometry_column_to_df


    # # Config
    # ready_data_db_uri = kwargs.get("ready_data_db_uri")
    # dag_infos = kwargs.get("dag_infos")
    # dag_id = dag_infos.get("dag_id")
    # load_behavior = dag_infos.get("load_behavior")
    # default_table = dag_infos.get("ready_data_default_table")
    # history_table = dag_infos.get("ready_data_history_table")
    # # Load



    # dataset.extend(fetch_city(2))

    # df = pd.DataFrame(dataset, columns=["星級", "停車場名稱", "地址"])
    # df.to_csv("~/Desktop/accessible_parking_flywheel.csv", index=False, encoding="utf-8-sig")
    # print("Done! 共抓到", len(df), "筆") 





    # gdata = add_point_wkbgeometry_column_to_df(
    #         data, x=data["elong"], y=data["nlat"], from_crs=4326
    #     )
    #     # select column
    # gdata = gdata.rename(
    #     columns={
    #         "elong": "longitude",
    #         "nlat": "latitude"
    #     }
    # )
    # data = gdata[["name", "type", "introduction", "address", "distric", "tel", "longitude", "latitude", "wkb_geometry"]]
    # data["data_time"] = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S")

    # engine = create_engine(ready_data_db_uri)
    # save_dataframe_to_postgresql(
    #     engine,
    #     data=data,
    #     load_behavior=load_behavior,
    #     default_table=default_table,
    #     history_table=history_table,
    # )
    # update_lasttime_in_data_to_dataset_info(
    #         engine, dag_id, data["data_time"].max()
    #     )

dag = CommonDag(proj_folder="proj_new_taipei_city_dashboard", dag_folder="accessible_facilities")
dag.create_dag(etl_func=_transfer)
