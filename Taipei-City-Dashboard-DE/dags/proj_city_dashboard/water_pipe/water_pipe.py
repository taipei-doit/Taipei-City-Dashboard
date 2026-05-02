from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import gzip
    import io
    import xml.etree.ElementTree as ET

    import geopandas as gpd
    import pandas as pd
    import requests
    from shapely.geometry import LineString
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

    resource_ids = [
        "30056122-21c3-4a6d-9f90-274509a08e7a",
        "aeeaa0cd-38f0-45f1-9849-762642fb77be",
        "07946ee4-3537-49c7-a964-606c995e02fe",
        "650ab113-454c-45ba-a8b5-32066265b1a2",
        "540545ed-5d58-43b3-b1c7-3f6d6e3c73c1",
        "984276ba-b66a-40f3-9ef1-4e5668b9a3da",
    ]
    base_url = (
        "https://data.taipei/api/dataset/"
        "af167303-0e5f-45dd-b624-a01f541565ce/resource/{resource_id}/download"
    )

    field_map = {
        "類別碼": "category_code",
        "識別碼": "pipe_uid",
        "起點編號": "start_node_id",
        "終點編號": "end_node_id",
        "管理單位": "manager",
        "作業區分": "operation_type",
        "timePosition": "time_position",
        "管線編號": "pipe_no",
        "尺寸單位": "diameter_unit",
        "管徑寬度": "diameter_width",
        "管徑高度": "diameter_height",
        "涵管條數": "pipe_count",
        "管線材料": "material",
        "起點埋設深度": "start_depth",
        "終點埋設深度": "end_depth",
        "管線長度": "pipe_length",
        "管線型態": "pipe_type",
        "使用狀態": "usage_status",
        "資料狀態": "data_status",
        "備註": "note",
        "輸送物質": "substance",
    }
    numeric_cols = [
        "diameter_width",
        "diameter_height",
        "pipe_count",
        "start_depth",
        "end_depth",
        "pipe_length",
    ]

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

    def geometry_from_pos_list(pos_list):
        values = [float(v) for v in pos_list.replace(",", " ").split()]
        stride = 3 if len(values) % 3 == 0 else 2
        coords = list(zip(values[0::stride], values[1::stride]))
        if len(coords) < 2:
            return None
        return LineString(coords)

    def get_descendant_text(elem, child_name):
        for child in elem.iter():
            if local_name(child.tag) == child_name:
                return (child.text or "").strip()
        return None

    def parse_records(xml_stream, source_resource_id):
        records = []
        for _, elem in ET.iterparse(xml_stream, events=("end",)):
            if local_name(elem.tag) != "UTL_管線_自來水":
                continue

            values = {}
            for child in list(elem):
                key = local_name(child.tag)
                text = (child.text or "").strip()
                if key in field_map:
                    values[field_map[key]] = text

            pos_list = get_descendant_text(elem, "posList")
            if pos_list and values:
                geometry = geometry_from_pos_list(pos_list)
                if geometry is not None:
                    values["source_resource_id"] = source_resource_id
                    values["geometry"] = geometry
                    records.append(values)
            elem.clear()
        return records

    rows = []
    for resource_id in resource_ids:
        url = base_url.format(resource_id=resource_id)
        response = requests.get(
            url,
            proxies=proxies,
            stream=True,
            timeout=300,
            verify=False,
        )
        response.raise_for_status()
        response.raw.decode_content = True
        prefix = response.raw.read(2)
        raw_stream = PrependStream(prefix, response.raw)
        stream = (
            gzip.GzipFile(fileobj=raw_stream)
            if prefix == b"\x1f\x8b"
            else raw_stream
        )
        rows.extend(parse_records(stream, resource_id))

    if not rows:
        raise ValueError("Water pipe XML resources returned no pipe records.")

    data = pd.DataFrame(rows)
    for col in numeric_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data[data["diameter_width"] > 400]

    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    data["segment_id"] = range(1, len(data) + 1)

    gdata = gpd.GeoDataFrame(data, geometry="geometry", crs="EPSG:3826")
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=3826, to_crs=4326)

    columns = [
        "data_time",
        "segment_id",
        "source_resource_id",
        "category_code",
        "pipe_uid",
        "start_node_id",
        "end_node_id",
        "manager",
        "operation_type",
        "time_position",
        "pipe_no",
        "diameter_unit",
        "diameter_width",
        "diameter_height",
        "pipe_count",
        "material",
        "start_depth",
        "end_depth",
        "pipe_length",
        "pipe_type",
        "usage_status",
        "data_status",
        "note",
        "substance",
        "wkb_geometry",
    ]
    ready_data = gdata[[col for col in columns if col in gdata.columns]]

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="LineString",
    )
    update_lasttime_in_data_to_dataset_info(
        engine,
        airflow_dag_id=dag_id,
        lasttime_in_data=get_tpe_now_time_str(is_with_tz=True),
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="water_pipe")
dag.create_dag(etl_func=_transfer)
