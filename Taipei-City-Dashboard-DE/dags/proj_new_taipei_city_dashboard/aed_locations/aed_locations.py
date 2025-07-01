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
    from utils.transform_address import (
        clean_data,
        main_process,
        save_data,
        get_addr_xy_parallel,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # Extract
    RID = "61b29f27-219a-4394-9722-af97a5707598"
    client = NewTaipeiAPIClient(RID, input_format="json")
    res = client.get_all_data(size=1000)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Transform
    raw_data = raw_data.rename(columns={
        "seqno": "seqno",
        "organizer": "organizer",
        "tel": "tel",
        "extension": "extension",
        "mobile telephone": "mobile_phone",
        "zipcode": "zipcode",
        "district": "district",
        "hosp_addr": "address",
        "type": "type",
        "location": "aed_location",
        "mon_stime": "mon_start",
        "mon_dtime": "mon_end",
        "tue_stime": "tue_start",
        "tue_dtime": "tue_end",
        "wed_stime": "wed_start",
        "wed_dtime": "wed_end",
        "thu_stime": "thu_start",
        "thu_dtime": "thu_end",
        "fri_stime": "fri_start",
        "fri_dtime": "fri_end",
        "sat_stime": "sat_start",
        "sat_dtime": "sat_end",
        "sun_stime": "sun_start",
        "sun_dtime": "sun_end",
        "remark": "remark",
        "date": "install_date",
        "battery expiration date": "battery_expiration",
        "electrical pads expiration date": "pads_expiration"
    })

    addr = raw_data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    _, output = save_data(addr, addr_cleaned, standard_addr_list)
    raw_data["address"] = output
    lng, lat = get_addr_xy_parallel(output)
    raw_data["lng"] = lng
    raw_data["lat"] = lat

    gdata = add_point_wkbgeometry_column_to_df(raw_data, raw_data["lng"], raw_data["lat"], from_crs=4326)

    ready_data = gdata[[
        "seqno", "organizer", "tel", "extension", "mobile_phone",
        "zipcode", "district", "address", "type", "aed_location",
        "mon_start", "mon_end", "tue_start", "tue_end",
        "wed_start", "wed_end", "thu_start", "thu_end",
        "fri_start", "fri_end", "sat_start", "sat_end",
        "sun_start", "sun_end", "remark", "install_date",
        "battery_expiration", "pads_expiration", "lng", "lat", "wkb_geometry", "data_time"
    ]]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point"
    )
    update_lasttime_in_data_to_dataset_info(engine, dag_id, ready_data["data_time"].max())

dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="aed_locations"
)
dag.create_dag(etl_func=_transfer)
