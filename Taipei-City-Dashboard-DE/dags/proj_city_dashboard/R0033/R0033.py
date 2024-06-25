from airflow import DAG
from operators.common_pipeline import CommonDag


def _R0033(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
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
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=577b3810-49b7-44fd-a5b7-97897bb50f9e"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    # Extract
    raw_data = pd.read_csv(URL)

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "項次編號": "id",
            "評分等級": "score",
            "認定項目": "case",
            "行政區編號": "district",
            "地址": "address",
            "場所名稱": "place",
        }
    )
    # map district name
    data["district"] = data["district"].astype(int)
    district_map = {
        63000010: "松山區",
        63000020: "信義區",
        63000030: "大安區",
        63000040: "中山區",
        63000050: "中正區",
        63000060: "大同區",
        63000070: "萬華區",
        63000080: "文山區",
        63000090: "南港區",
        63000100: "內湖區",
        63000110: "士林區",
        63000120: "北投區",
    }
    data["district"] = data["district"].replace(district_map)
    # geocoding
    addr = "臺北市" + data["district"] + data["address"]
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    x, y = get_addr_xy_parallel(output)
    # geometry
    gdata = add_point_wkbgeometry_column_to_df(data, x, y, from_crs=FROM_CRS)
    # select columns
    ready_data = gdata.drop(columns=["geometry", "lng", "lat"])

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )
    update_lasttime_in_data_to_dataset_info(engine, dag_id)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0033")
dag.create_dag(etl_func=_R0033)
