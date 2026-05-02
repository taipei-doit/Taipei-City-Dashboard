from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import gzip
    import io
    import re
    import xml.etree.ElementTree as ET
    from datetime import date

    import geopandas as gpd
    import pandas as pd
    import requests
    from shapely.geometry import Point
    from sqlalchemy import create_engine
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import convert_geometry_to_wkbgeometry

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    url = (
        "https://data.taipei/api/dataset/"
        "44c6fb09-8f51-403a-95a8-99a2387c2f05/resource/"
        "2046c65f-024f-4ded-ad25-5349b66a41ed/download"
    )
    field_map = {
        "類別碼": "category_code",
        "識別碼": "valve_uid",
        "管理單位": "manager",
        "作業區分": "operation_type",
        "開關閥編號": "switch_valve_no",
        "閥類編號": "valve_no",
        "口徑": "diameter",
        "名稱": "name",
        "地盤高": "ground_elevation",
        "埋設深度": "buried_depth",
        "開關閥型態": "valve_type",
        "使用狀態": "usage_status",
        "資料狀態": "data_status",
        "備註": "note",
    }

    class PrependStream:
        def __init__(self, prefix, stream):
            self.prefix = io.BytesIO(prefix)
            self.stream = stream

        def read(self, size=-1):
            prefix_data = self.prefix.read(size)
            if size != -1 and len(prefix_data) == size:
                return prefix_data
            rest_size = -1 if size == -1 else size - len(prefix_data)
            return prefix_data + self.stream.read(rest_size)

    def local_name(tag):
        return tag.rsplit("}", 1)[-1]

    def get_descendant_text(elem, child_name):
        for child in elem.iter():
            if local_name(child.tag) == child_name:
                value = (child.text or "").strip()
                if value:
                    return value
        return None

    def parse_float(value):
        if not value:
            return None
        match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
        return float(match.group(0)) if match else None

    def parse_install_date(value):
        if not value:
            return None
        install_date = pd.to_datetime(value, errors="coerce")
        if pd.isna(install_date) or install_date.year == 1912:
            return None
        return install_date.date()

    def parse_point(value):
        if not value:
            return None
        coords = [float(v) for v in value.replace(",", " ").split()]
        if len(coords) < 2:
            return None
        return Point(coords[0], coords[1])

    def valve_age_years(install_date):
        if not install_date:
            return None
        today = date.today()
        return today.year - install_date.year - (
            (today.month, today.day) < (install_date.month, install_date.day)
        )

    response = requests.get(url, proxies=proxies, stream=True, timeout=300, verify=False)
    response.raise_for_status()
    response.raw.decode_content = True
    prefix = response.raw.read(2)
    raw_stream = PrependStream(prefix, response.raw)
    stream = gzip.GzipFile(fileobj=raw_stream) if prefix == b"\x1f\x8b" else raw_stream

    rows = []
    for _, elem in ET.iterparse(stream, events=("end",)):
        if local_name(elem.tag) != "UTL_開關閥":
            continue

        values = {}
        for child in list(elem):
            key = local_name(child.tag)
            if key in field_map:
                values[field_map[key]] = (child.text or "").strip()

        install_date = parse_install_date(get_descendant_text(elem, "timePosition"))
        geometry = parse_point(get_descendant_text(elem, "coordinates"))
        if geometry is None:
            elem.clear()
            continue

        values["install_date"] = install_date
        values["valve_age_years"] = valve_age_years(install_date)
        values["diameter"] = parse_float(values.get("diameter"))
        values["ground_elevation"] = parse_float(values.get("ground_elevation"))
        values["buried_depth"] = parse_float(values.get("buried_depth"))
        values["geometry"] = geometry
        rows.append(values)
        elem.clear()

    if not rows:
        raise ValueError("Water valve XML returned no records.")

    data = pd.DataFrame(rows)
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    data["valve_id"] = range(1, len(data) + 1)

    gdata = gpd.GeoDataFrame(data, geometry="geometry", crs="EPSG:3826")
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=3826, to_crs=4326)

    columns = [
        "data_time",
        "valve_id",
        "category_code",
        "valve_uid",
        "manager",
        "operation_type",
        "install_date",
        "valve_age_years",
        "switch_valve_no",
        "valve_no",
        "diameter",
        "name",
        "ground_elevation",
        "buried_depth",
        "valve_type",
        "usage_status",
        "data_status",
        "note",
        "wkb_geometry",
    ]

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=gdata[[col for col in columns if col in gdata.columns]],
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point",
    )
    update_lasttime_in_data_to_dataset_info(
        engine,
        airflow_dag_id=dag_id,
        lasttime_in_data=get_tpe_now_time_str(is_with_tz=True),
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="water_valve")
dag.create_dag(etl_func=_transfer)
