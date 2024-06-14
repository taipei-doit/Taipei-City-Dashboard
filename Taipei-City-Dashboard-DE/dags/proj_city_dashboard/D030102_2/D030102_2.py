from airflow import DAG
from operators.common_pipeline import CommonDag


def D030102_2(**kwargs):
    import xml.etree.ElementTree as ET

    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import LineString
    from sqlalchemy import create_engine
    from utils.extract_stage import (
        download_file,
        get_data_taipei_file_last_modified_time,
    )
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import (
        convert_geometry_to_wkbgeometry,
        convert_linestring_to_multilinestring,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=0912d803-688f-493a-b682-27da729ed593"
    PAGE_ID = "4fefd1b3-58b9-4dab-af00-724c715b0c58"
    GEOMETRY_TYPE = "MultiLineStringZ"
    file_name = f"{dag_id}.kml"
    FROM_CRS = 4326

    # Extract
    # get xml tree
    local_file = download_file(file_name, URL)
    if not local_file:
        return False
    tree = ET.parse(local_file)
    root = tree.getroot()
    # parse kml
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    results = {
        "item": [],
        "name": [],
        "description": [],
        "length": [],
        "geometry": [],
        "route": [],
    }
    for placemark in root.findall(".//kml:Placemark", ns):
        name = placemark.find(".//kml:name", ns).text
        explan_element = placemark.find(
            './/kml:ExtendedData/kml:SchemaData/kml:SimpleData[@name="Explan"]', ns
        )
        description = explan_element.text if explan_element is not None else ""
        for simpledata in placemark.findall(".//kml:SimpleData", ns):
            if simpledata.attrib["name"] == "length_M_":
                length = simpledata.text
        fid_element = placemark.find(
            './/kml:ExtendedData/kml:SchemaData/kml:SimpleData[@name="fid"]', ns
        )
        item = int(fid_element.text) if fid_element is not None else int(0)
        coordinates = placemark.find(".//kml:LineString/kml:coordinates", ns).text
        coordinates_list = [
            tuple(map(float, coord.split(","))) for coord in coordinates.split()
        ]
        linestring = LineString(coordinates_list)
        # append to results
        results["item"].append(item)
        results["name"].append(name)
        results["description"].append(description)
        results["length"].append(length)
        results["geometry"].append(linestring)
        results["route"].append("")
    raw_data = gpd.GeoDataFrame(results, crs=FROM_CRS)
    raw_data['data_time'] = get_data_taipei_file_last_modified_time(PAGE_ID)

    # Transform
    gdata = raw_data.copy()
    # substring
    gdata["cost_time"] = gdata["description"].str.extract("（約(.*)分鐘）")
    # define column type
    gdata["cost_time"] = pd.to_numeric(gdata["cost_time"], errors="coerce")
    gdata["length"] = pd.to_numeric(gdata["cost_time"], errors="coerce")
    gdata["item"] = gdata["item"].astype(int)
    gdata["item"] = gdata["item"].astype(str)
    # time
    gdata["data_time"] = convert_str_to_time_format(gdata["data_time"])
    # geometry
    gdata["geometry"] = gdata["geometry"].apply(convert_linestring_to_multilinestring)
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    gdata = gdata.drop(columns=["geometry"])
    # select column
    ready_data = gdata[
        [
            "data_time",
            "item",
            "route",
            "name",
            "length",
            "cost_time",
            "description",
            "wkb_geometry",
        ]
    ]

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
    lasttime_in_data = gdata["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D030102_2")
dag.create_dag(etl_func=D030102_2)
