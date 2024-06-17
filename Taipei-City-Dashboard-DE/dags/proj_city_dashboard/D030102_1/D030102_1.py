from airflow import DAG
from operators.common_pipeline import CommonDag


def D030102_1(**kwargs):
    import xml.etree.ElementTree as ET

    import geopandas as gpd
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
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=a69988de-6a49-4956-9220-40ebd7c42800"
    PAGE_ID = f"89202d05-0e3e-4781-a04f-45327bf12b30"
    GEOMETRY_TYPE = "LineStringZ"
    EMPTY_LINESTRING = None
    FROM_CRS = 4326
    file_name = f"{dag_id}.kml"

    # Extract
    # get xml tree
    local_file = download_file(file_name, URL)
    if not local_file:
        return False
    tree = ET.parse(local_file)
    root = tree.getroot()
    # parse kml
    results = {
        "id": [],
        "city": [],
        "name": [],
        "start_road": [],
        "end_road": [],
        "description": [],
        "geometry": [],
    }
    for placemark in root.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
        linestring = placemark.find(".//{http://www.opengis.net/kml/2.2}LineString")
        if linestring is None:
            results["geometry"].append(EMPTY_LINESTRING)
        else:
            # geometry
            coordinates = linestring.find(
                "{http://www.opengis.net/kml/2.2}coordinates"
            ).text
            coords = [
                tuple(map(float, coord.split(",")))
                for coord in coordinates.strip().split()
            ]
            is_not_valid_linestring = len(coords) < 2
            if is_not_valid_linestring:
                results["geometry"].append(EMPTY_LINESTRING)
            else:
                linestring = LineString(coords)
                results["geometry"].append(linestring)
        # description
        desc = placemark.find("{http://www.opengis.net/kml/2.2}description").text
        results["description"].append(desc)
        # other columns
        descriptions = desc.split("\n")
        desc_dict = {}
        for description in descriptions:
            if description == "":
                continue
            else:
                key, value = description.split("：")
                desc_dict[key] = value
        # append to results
        results["city"].append(desc_dict.get("縣市別"))
        results["start_road"].append(desc_dict.get("起點描述"))
        results["end_road"].append(desc_dict.get("迄點描述"))
        results["id"].append(desc_dict.get("編號"))
        results["name"].append(desc_dict.get("名稱"))
    raw_data = gpd.GeoDataFrame(results, crs=FROM_CRS)
    raw_data["data_time"] = get_data_taipei_file_last_modified_time(PAGE_ID)

    # Transform
    gdata = raw_data.copy()
    # time
    gdata["data_time"] = convert_str_to_time_format(gdata["data_time"])
    # geometry
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=FROM_CRS)
    gdata = gdata.drop(columns=["geometry"])
    # select column
    ready_data = gdata[
        [
            "data_time",
            "id",
            "city",
            "name",
            "start_road",
            "end_road",
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


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D030102_1")
dag.create_dag(etl_func=D030102_1)
