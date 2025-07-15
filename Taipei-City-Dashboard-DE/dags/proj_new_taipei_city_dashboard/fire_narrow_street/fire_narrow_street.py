from airflow import DAG
from operators.common_pipeline import CommonDag


# 定義 Airflow DAG 要執行的 ETL 任務函式
def _transfer(**kwargs):
    
    """
            [
            {
                "seqno": "1",
                "district": "板橋區",
                "fire branch": "板橋分隊",
                "location": "館前西路213巷",
                "the width and length": "寬度約:2.1\n長度約:150"
            },
            {
                "seqno": "2",
                "district": "板橋區",
                "fire branch": "板橋分隊",
                "location": "華興街21巷",
                "the width and length": "寬度約:4.7\n長度約:150"
            }]
            
                data_time timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
                "type" varchar(10) NULL,
                fire_brigade varchar(20) NULL,
                county varchar(5) NULL,
                town varchar(5) NULL,
                street text NULL,
                width_meter float8 NULL,
                note text NULL,
                wkb_geometry public.geometry(multilinestring, 4326) NULL,
      """
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from utils.get_time import get_tpe_now_time_str
    from utils.transform_address import get_addr_xy_parallel
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.extract_stage import NewTaipeiAPIClient
    from utils.transform_address import (
        clean_data,
        get_addr_xy_parallel,
        main_process,
        save_data,
    )

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"
    RID= "5e5bd1b4-b5fd-406b-84c4-ae2d70d2ba71"
    client = NewTaipeiAPIClient(RID, input_format="json")
    res = client.get_all_data(size=1000)

    data = pd.DataFrame(res)

    col_map = {
        "fire branch": "fire_brigade",
        "location": "street",
        "district": "town",
        "the width and length": "width_meter"
    }
    data = data.rename(columns=col_map)

    data['county'] = '新北市'
    data['width_meter'] = data['width_meter'].str.extract(r'寬度約:([0-9.]+)')
    data['width_meter'] = data['width_meter'].astype(float)    
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    data['address'] = '新北市' + data['town'] + data['street'].fillna('')
        # get geometry

    addr = data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    data["address"] = output
    # get gis xy
    data["longitude"], data["latitude"] = get_addr_xy_parallel(output)
    # standarlize geometry
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    )
    # select column
    ready_data = gdata[
        [
            "data_time",
            "fire_brigade",
            "county",
            "street",
            "town",
            "width_meter",
            "wkb_geometry",
        ]
    ]


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
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )

# 建立 DAG 物件，指定專案與 DAG 所在目錄
dag = CommonDag(
    proj_folder='proj_new_taipei_city_dashboard',
    dag_folder='fire_narrow_street'
)

# 將 _transfer 函式掛載為 DAG 的主要 ETL 任務
dag.create_dag(etl_func=_transfer)
