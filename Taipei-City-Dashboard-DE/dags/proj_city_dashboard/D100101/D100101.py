from airflow import DAG
from operators.common_pipeline import CommonDag


def remove_district_code(x):
    if isinstance(x, str) and "630" in x:
        city = x[:3]
        rest = x[11:]
        return f"{city}{rest}"
    else:
        print("無須轉換:" + x)
        return x


def D100101(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        get_data_taipei_file_last_modified_time,
        get_data_taipei_api,
    )
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_address import get_addr_xy_parallel
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    raw_data_db_uri = kwargs.get("raw_data_db_uri")
    data_folder = kwargs.get("data_folder")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    # Manually set
    RID = "4350117f-8697-4903-8a49-a7a59f30eeb1"
    PAGE_ID = "5d1d34d8-1b81-4162-87b6-05e0896af958"
    FROM_CRS = 4326

    # Extract
    res = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)

    # Transform
    # Rename
    data = raw_data
    data = data.drop(columns=["_id", "_importdate"])
    data = data.rename(
        columns={
            "行政區": "district",
            "機構名稱": "name",
            "地址": "addr",
            "電話": "phone",
            "分機": "extension",
            "手機": "cellphone",
            "開放時間": "open_time",
            "位置指引": "location_guide",
            "基本設備": "basic_equipment",
            "友善設備或服務": "friendly_equipment",
            "優良哺集乳室認證效期": "certification_effective_period",
            "輪椅使用": "wheelchair_use",
            "貼心小提醒": "reminder",
        }
    )
    # Mapping district and replace ZIP code in addr
    district_map = {
        63000040: "中山區",
        63000050: "中正區",
        63000020: "信義區",
        63000100: "內湖區",
        63000120: "北投區",
        63000090: "南港區",
        63000110: "士林區",
        63000060: "大同區",
        63000030: "大安區",
        63000080: "文山區",
        63000010: "松山區",
        63000070: "萬華區",
    }
    data["district"] = data["district"].astype(int)
    data["district"] = data["district"].map(district_map)
    data["addr"] = data["addr"].apply(remove_district_code)
    data["addr"] = (
        data["addr"].str[:3].str.cat(data["district"], sep="") + data["addr"].str[3:]
    )
    # Replace seperations of facility descriptions and extract friendly equipment
    data["friendly_equipment"] = data["friendly_equipment"].apply(
        lambda x: x.replace(";", "、")
    )
    data["basic_equipment"] = data["basic_equipment"].apply(
        lambda x: x.replace(";", "、")
    )
    data["diaper_changing_table"] = data["friendly_equipment"].apply(
        lambda x: True if isinstance(x, str) and "尿布台" in x else False
    )
    data["storage_space"] = data["friendly_equipment"].apply(
        lambda x: True if isinstance(x, str) and "置物空間" in x else False
    )
    data["stroller_parking"] = data["friendly_equipment"].apply(
        lambda x: True if isinstance(x, str) and "嬰兒車停放空間" in x else False
    )
    data["drinking_water"] = data["friendly_equipment"].apply(
        lambda x: True if isinstance(x, str) and "飲水服務" in x else False
    )
    data["fridge"] = data["friendly_equipment"].apply(
        lambda x: True if isinstance(x, str) and "母乳專用冰箱" in x else False
    )
    # Time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    # Geometry
    data["lng"], data["lat"] = get_addr_xy_parallel(data["addr"], sleep_time=0.5)
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=FROM_CRS
    )
    # Reshape
    ready_data = gdata.drop(columns=["lng", "lat", "geometry", "cellphone"])

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point",
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100101")
dag.create_dag(etl_func=D100101)
