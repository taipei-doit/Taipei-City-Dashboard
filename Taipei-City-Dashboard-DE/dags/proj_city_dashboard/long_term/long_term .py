from airflow import DAG
from operators.common_pipeline import CommonDag

def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_api
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

    # Extract from two sources
    rid_private = "9a3e0440-87ea-4793-9240-5c8dc02b5129"
    rid_public = "67549b46-4328-48d3-973f-dd7d3a96dbed"

    df_private = pd.DataFrame(get_data_taipei_api(rid_private))
    df_public = pd.DataFrame(get_data_taipei_api(rid_public))

    # Combine data
    raw_data = pd.concat([df_private, df_public], ignore_index=True)
    raw_data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

    # Rename columns
    raw_data = raw_data.rename(columns={
        "_id": "place_id",
        "屬性": "property",
        "機構名稱": "place_name",
        "區域別": "zone",
        "地址": "address",
        "電話": "tel",
        "收容對象": "target_group",
        "核定總床位數量": "bed_total",
        "長照床位數量": "bed_longterm",
        "養護床位數量": "bed_nursing",
        "失智床位數量": "bed_dementia",
        "安養床位數量": "bed_retirement"
    })

    # Add city field
    raw_data["city"] = raw_data["address"].str[:3]

    # Geocode address to get lat/lng
    addr = raw_data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    _, output = save_data(addr, addr_cleaned, standard_addr_list)
    raw_data["address"] = output
    lng, lat = get_addr_xy_parallel(output)
    raw_data["lng"] = lng
    raw_data["lat"] = lat

    # Geometry
    gdf = add_point_wkbgeometry_column_to_df(raw_data, raw_data["lng"], raw_data["lat"], from_crs=4326)

    # Select columns
    ready_data = gdf[[
        "place_id", "property", "place_name", "zone", "address", "tel",
        "target_group", "bed_total", "bed_longterm", "bed_nursing",
        "bed_dementia", "bed_retirement", "city", "lng", "lat",
        "wkb_geometry", "data_time"
    ]]

    # ✅ 加這行，過濾無效點位
    ready_data = ready_data[
        ready_data["wkb_geometry"].notnull() &
        ready_data["lat"].notnull() &
        ready_data["lng"].notnull()
    ]
    # Load to PostgreSQL
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point"
    )

    # Update metadata
    update_lasttime_in_data_to_dataset_info(
        engine,
        dag_id,
        ready_data["data_time"].max()
    )

# Create DAG
dag = CommonDag(
    proj_folder="proj_city_dashboard",
    dag_folder="long_term"
)
dag.create_dag(etl_func=_transfer)
