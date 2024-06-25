from airflow import DAG
from operators.common_pipeline import CommonDag


def extarct_license_from_xml(filename, url):
    import xml.etree.ElementTree as ET

    import pandas as pd
    from utils.extract_stage import download_file

    # download
    local_file = download_file(filename, url)

    # parse xml
    tree = ET.parse(local_file)
    root = tree.getroot()
    df_list = []
    for _license in root:
        temp = {}
        # A license could have multiple land units and multiple buildings.
        # For our purpose, we divide each land unit into a row.
        number_of_land_units = len(_license.find("地段地號"))
        for index_of_land_unit in range(number_of_land_units):
            # dynamic construct each column
            for col in _license:
                if col.tag == "地段地號":
                    temp[col.tag] = col[index_of_land_unit].text
                if col.tag == "建築地點":
                    # dashboard show a point for a license, so only need to extract the first building address.
                    temp[col.tag] = col[0].text if len(col) > 0 else None
                elif col.tag in ["建物資訊", "建物面積", "地段地號"]:
                    # some info have sub item and not a fixed length, so need to loop to extract.
                    for sub_info in col:
                        temp[sub_info.tag] = sub_info.text
                else:
                    temp[col.tag] = col.text
            df_list.append(temp)
    return pd.DataFrame(df_list)


def transform_license(new_data, from_crs):
    import pandas as pd
    from utils.transform_address import (
        clean_data,
        get_addr_xy_parallel,
        main_process,
        save_data,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    # rename
    new_data = new_data.rename(columns={"工程金額": "工程造價"})

    # clean address
    new_data["建築地點_點位"] = new_data["建築地點"].str.split(" ").str[0]
    addr = pd.Series(new_data["建築地點_點位"].unique())

    # get gis x, y from address
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    x, y = get_addr_xy_parallel(output)

    # merge x, y back to data
    temp = pd.DataFrame({"lng": x, "lat": y, "建築地點_點位": output})
    new_data = pd.merge(new_data, temp, on="建築地點_點位", how="left")

    # standardize gis
    new_gdata = add_point_wkbgeometry_column_to_df(
        new_data, new_data["lng"], new_data["lat"], from_crs=from_crs
    )

    # reshape
    new_gdata = new_gdata[
        [
            "建築地點",
            "建築地點_點位",
            "執照年度",
            "執照號碼",
            "發照日期",
            "設計人",
            "監造人",
            "建造類別",
            "構造種類",
            "使用分區",
            "棟數",
            "地上層數",
            "地下層數",
            "戶數",
            "騎樓基地面積",
            "其他基地面積",
            "建築面積",
            "工程造價",
            "地段地號",
            "wkb_geometry",
        ]
    ]
    ready_data = new_gdata.drop_duplicates()
    return ready_data


def _R0059(**kwargs):
    from sqlalchemy import create_engine
    from utils.extract_stage import get_data_taipei_file_last_modified_time
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=74a8b311-906e-44c4-91fb-7f413842d4e1"
    filename = f"{dag_id}.xml"
    PAGE_ID = "0816f991-e6c8-4da0-a789-d022fee1462b"
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # Extract
    raw_data = extarct_license_from_xml(filename, URL)

    # Transform
    ready_data = transform_license(raw_data, FROM_CRS)

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        geometry_type=GEOMETRY_TYPE,
    )

    # Update dataset_info whether there is new data or not
    engine = create_engine(ready_data_db_uri)
    lasttime_in_data = get_data_taipei_file_last_modified_time(PAGE_ID)
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0059")
dag.create_dag(etl_func=_R0059)
