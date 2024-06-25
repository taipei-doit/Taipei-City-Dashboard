from airflow import DAG
from operators.common_pipeline import CommonDag


def extarct_permit_from_xml(file_path, url, page_id, time_out=60):
    import xml.etree.ElementTree as ET

    import pandas as pd
    import requests
    from utils.extract_stage import get_data_taipei_file_last_modified_time

    # download XML
    res = requests.get(url, timeout=time_out)
    if res.status_code != 200:
        raise ValueError(f"Request Error: {res.status_code}")
    with open(file_path, "wb") as f:
        f.write(res.content)

    # parse xml
    tree = ET.parse(file_path)
    root = tree.getroot()
    temps = []
    for permit in root:
        temp = {}
        # A permit could have multiple land units.
        # For our purpose, we divide each land unit into a row.
        number_of_land_units = len(permit.find("地段地號"))
        for index_of_land_unit in range(number_of_land_units):
            # dynamic construct each column
            for col in permit:
                if col.tag == "地段地號":
                    temp[col.tag] = col[index_of_land_unit].text
                if col.tag == "建築地點":
                    # dashboard show a point for a permit, so only need to extract the first building address.
                    temp[col.tag] = col[0].text if len(col) > 0 else None
                elif col.tag in ["建物資訊", "建物面積", "地段地號"]:
                    # some info have sub item and not a fixed length, so need to loop to extract.
                    for sub_info in col:
                        temp[sub_info.tag] = sub_info.text
                else:
                    temp[col.tag] = col.text
            temps.append(temp)
    raw_data = pd.DataFrame(temps)

    # add updata time
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(page_id)
    return raw_data


def get_cadastral(engine):
    import pandas as pd

    sql = """
        SELECT thekey, thename, thelink,
            aa48, aa49, aa10, aa21, aa22,
            kcnt, cada_text, aa17, aa16, aa46,
            ST_AsText(wkb_geometry) as geometry
        FROM building_cadastralmap
    """
    cadastral = pd.read_sql(sql, con=engine)
    cadastral["kcnt"] = cadastral["kcnt"].astype(str)
    cadastral["aa49"] = cadastral["aa49"].astype(str).str.zfill(8)
    cadastral["key"] = cadastral["kcnt"] + cadastral["aa49"]
    return cadastral


def transform_permit(raw_data, from_crs, engine):
    import geopandas as gpd
    from utils.transform_geometry import (
        convert_geometry_to_wkbgeometry,
        convert_polygon_to_multipolygon,
    )
    from utils.transform_time import convert_str_to_time_format

    data = raw_data.copy()

    # rename
    data = data.rename(
        columns={
            "執照號碼": "110年建造執照2_執照號碼",
            "發照日期": "110年建造執照2_發照日期",
        }
    )

    # standardize time
    data["data_time"] = convert_str_to_time_format(data["data_time"])
    data["發照日"] = convert_str_to_time_format(
        data["110年建造執照2_發照日期"], from_format="%TY%m%d"
    )
    data["epoch_time"] = data["發照日"].map(lambda x: x.timestamp())

    # mapping data to get geometry
    # get cadastral

    cadastral = get_cadastral(engine)
    # add merge key
    data["cadastral map_key_地籍圖key值"] = data["地段地號"].str.split("區").str[1]
    data["cadastral map_key_地籍圖key值"] = (
        data["cadastral map_key_地籍圖key值"].str.replace("號", "").str.replace("-", "")
    )
    # join table
    join_data = data.merge(
        cadastral, how="inner", left_on="cadastral map_key_地籍圖key值", right_on="key"
    )

    # standardize geometry
    join_data["geometry"] = gpd.GeoSeries.from_wkt(
        join_data["geometry"], crs=f"EPSG:{from_crs}"
    )
    gdata = gpd.GeoDataFrame(join_data, crs=f"EPSG:{from_crs}", geometry="geometry")
    gdata["geometry"] = gdata["geometry"].apply(convert_polygon_to_multipolygon)
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=from_crs)

    # select columns
    ready_data = gdata[
        [
            "thekey",
            "thename",
            "thelink",
            "aa48",
            "aa49",
            "aa10",
            "aa21",
            "aa22",
            "kcnt",
            "cada_text",
            "aa17",
            "aa16",
            "aa46",
            "cadastral map_key_地籍圖key值",
            "110年建造執照2_發照日期",
            "110年建造執照2_執照號碼",
            "發照日",
            "epoch_time",
            "wkb_geometry",
        ]
    ]
    return ready_data


def _R0057(**kwargs):
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    # Comfig
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=43624c8e-c768-4b3c-93c4-595f5af7a9cb"
    file_path = f"{data_path}/{dag_id}.xml"
    PAGE_ID = "d8834353-ff8e-4a6c-9730-a4d3541f2669"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "MultiPolygon"

    # Extract
    raw_data = extarct_permit_from_xml(file_path, URL, PAGE_ID)

    # Transform
    engine = create_engine(ready_data_db_uri)
    ready_data = transform_permit(raw_data, FROM_CRS, engine)

    # Load
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        geometry_type=GEOMETRY_TYPE,
    )
    lasttime_in_data = ready_data["發照日"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0057")
dag.create_dag(etl_func=_R0057)
