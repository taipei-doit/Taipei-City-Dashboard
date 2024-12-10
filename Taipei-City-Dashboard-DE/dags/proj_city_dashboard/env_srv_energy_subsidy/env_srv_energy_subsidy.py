from airflow import DAG
from operators.common_pipeline import CommonDag
import pandas as pd
from sqlalchemy import create_engine
from utils.extract_stage import get_data_taipei_api
from utils.load_stage import (
    save_geodataframe_to_postgresql,
    update_lasttime_in_data_to_dataset_info, save_dataframe_to_postgresql
)
from datetime import datetime
from utils.transform_address import (
    clean_data,
    get_addr_xy_parallel,
    main_process,
    save_data,
)
from utils.transform_geometry import add_point_wkbgeometry_column_to_df
from utils.transform_time import convert_str_to_time_format


dag_id = "env_srv_energy_subsidy"


def _transfer(**kwargs):


    ##############
    ## get config
    ##############
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID = "5f239e5c-9388-4dc2-b6a6-f65491edd78a"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    ##############
    ## Extract
    ##############
    raw_list = get_data_taipei_api(RID)
    print(raw_list)
    raw_data = pd.DataFrame(raw_list)
    print(raw_data)
    # raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]


    ##############
    ## Transform
    ##############
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "年度": "data_year",
            "核撥件數": "num_of_approval",
            "累積核撥件數": "acc_num_of_approval",
            "補助金額": "subsidy_amt",
            "累計補助金額": "acc_subsidy_amt",
            "節電量": "enegry_saving_amt",
            "累積節電量": "acc_enegry_saving_amt",
        }
    )


    # 將民國年份轉為西元年份
    data["data_time"] = data["data_year"].astype(int) + 1911

    # 將年份轉為 datetime 格式，假設日期為 12 月 31 日
    data["data_time"] = pd.to_datetime(data["data_time"].astype(str) + "-12-31")

    # 將 datetime 格式轉為指定的字串格式，並加上固定時區偏移
    data["data_time"] = data["data_time"].dt.strftime("%Y-%m-%d %H:%M:%S+08")


    print(data)
    # 整數轉換
    data["num_of_approval"] = data["num_of_approval"].apply(lambda x:x.replace(",","")).astype('int')
    data["acc_num_of_approval"] = data["acc_num_of_approval"].apply(lambda x:x.replace(",","")).astype('int')
    data["subsidy_amt"] = data["subsidy_amt"].apply(lambda x:x.replace(",","")).astype('int')
    data["acc_subsidy_amt"] = data["acc_subsidy_amt"].apply(lambda x:x.replace(",","")).astype('int')
    data["enegry_saving_amt"] = data["enegry_saving_amt"].apply(lambda x:x.replace(",","")).astype('int')
    data["acc_enegry_saving_amt"] = data["acc_enegry_saving_amt"].apply(lambda x:x.replace(",","")).astype('int')

    

    # # standardize time
    # data["etl_dtm"] = convert_str_to_time_format(data["etl_dtm"])
    # # geocoding
    # addr = data["address"]
    # addr_cleaned = clean_data(addr)
    # standard_addr_list = main_process(addr_cleaned)
    # result, output = save_data(addr, addr_cleaned, standard_addr_list)
    # data["address"] = output
    # unique_addr = pd.Series(output.unique())
    # x, y = get_addr_xy_parallel(unique_addr)
    # temp = pd.DataFrame({"lng": x, "lat": y, "address": unique_addr})
    # data = pd.merge(data, temp, on="address", how="left")
    # # add town
    # town_pattern = "(中正|大同|中山|松山|大安|萬華|信義|士林|北投|內湖|南港|文山)區"
    # data["town"] = data["address"].str.extract(town_pattern, expand=False) + "區"
    # data.loc[data["town"] == "區", "town"] = ""
    # # define columns
    # data["lng"] = pd.to_numeric(data["lng"], errors="coerce")
    # data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    # # geometry
    # gdata = add_point_wkbgeometry_column_to_df(
    #     data, data["lng"], data["lat"], from_crs=FROM_CRS
    # )

    keep_col = [
            "data_time",
            "data_year",
             "num_of_approval",
             "acc_num_of_approval",
             "subsidy_amt",
             "acc_subsidy_amt",
             "enegry_saving_amt",
             "acc_enegry_saving_amt"
    ]




    # select columns
    ready_data = data[keep_col]

    # Load
    engine = create_engine(ready_data_db_uri)

    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        # geometry_type=GEOMETRY_TYPE,
    )
    # lasttime_in_data = data["data_time"].max()
    # update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder= dag_id)
dag.create_dag(etl_func=_transfer)