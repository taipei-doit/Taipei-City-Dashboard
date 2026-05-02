import zipfile
import xml.etree.ElementTree as ET
import geopandas as gpd
import pandas as pd
from airflow import DAG
from sqlalchemy import create_engine
from operators.common_pipeline import CommonDag
from utils.load_stage import (
    save_geodataframe_to_postgresql,
    update_lasttime_in_data_to_dataset_info,
)
from utils.transform_address import get_addr_xy_parallel
from utils.transform_geometry import add_point_wkbgeometry_column_to_df
from utils.get_time import get_tpe_now_time_str


def _parse_ooxml_excel(file_path: str) -> pd.DataFrame:
    """
    Parse Excel file using OOXML namespace.
    The provided Excel files use http://purl.oclc.org/ooxml/spreadsheetml/main
    which is not readable by standard openpyxl.
    """
    ns = "http://purl.oclc.org/ooxml/spreadsheetml/main"

    with zipfile.ZipFile(file_path) as z:
        with z.open("xl/sharedStrings.xml") as f:
            ss_root = ET.fromstring(f.read())
        strings = []
        for si in ss_root.iter(f"{{{ns}}}si"):
            t = si.find(f".//{{{ns}}}t")
            strings.append(t.text if t is not None else "")

        with z.open("xl/worksheets/sheet1.xml") as f:
            ws_root = ET.fromstring(f.read())

        rows = []
        for row in ws_root.iter(f"{{{ns}}}row"):
            row_data = []
            for cell in row.iter(f"{{{ns}}}c"):
                v = cell.find(f"{{{ns}}}v")
                if v is not None:
                    if cell.get("t") == "s":
                        row_data.append(strings[int(v.text)])
                    else:
                        row_data.append(v.text)
                else:
                    row_data.append("")
            rows.append(row_data)

    df = pd.DataFrame(rows[1:], columns=rows[0])
    return df


def _transfer(**kwargs):
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    data_path = kwargs.get("data_path")
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # 1. Extract raw data from both Excel files
    df_tpe = _parse_ooxml_excel(f"{data_path}/raw_data/環保杯_台北市.xlsx")
    df_ntpc = _parse_ooxml_excel(f"{data_path}/raw_data/環保杯_新北市.xlsx")
    raw_data = pd.concat([df_tpe, df_ntpc], ignore_index=True)
    raw_data["data_time"] = get_tpe_now_time_str()

    # Normalize column names
    raw_data = raw_data.rename(
        columns={
            "連鎖品牌": "brand",
            "縣市別": "city",
            "門市名稱": "store_name",
            "門市地址": "address",
            "門市電話": "phone",
        }
    )

    # Extract district from address (e.g. "臺北市大安區..." -> "大安區")
    raw_data["district"] = raw_data["address"].str[3:6]

    # 2. Geocode addresses to coordinates
    # Clean address for geocoding (remove floor/room info in parentheses)
    clean_addr = raw_data["address"].str.replace(r"\(.*\)", "", regex=True)
    lon, lat = get_addr_xy_parallel(clean_addr.tolist(), sleep_time=0.5)
    raw_data["lon"] = pd.to_numeric(lon, errors="coerce")
    raw_data["lat"] = pd.to_numeric(lat, errors="coerce")

    # Filter out rows without coordinates
    raw_data = raw_data.dropna(subset=["lon", "lat"]).copy()

    # 3. Build ready data DataFrame
    ready_data = pd.DataFrame({
        "brand": raw_data["brand"],
        "store_name": raw_data["store_name"],
        "address": raw_data["address"],
        "city": raw_data["city"],
        "district": raw_data["district"],
        "phone": raw_data["phone"],
        "lon": raw_data["lon"],
        "lat": raw_data["lat"],
        "data_time": raw_data["data_time"],
    })

    # 4. Add WKB geometry column
    gdata = add_point_wkbgeometry_column_to_df(
        ready_data,
        ready_data["lon"],
        ready_data["lat"],
        from_crs=FROM_CRS,
    )

    # 5. Load to PostgreSQL
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=gdata,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )

    update_lasttime_in_data_to_dataset_info(
        engine,
        airflow_dag_id=dag_id,
        lasttime_in_data=raw_data["data_time"].max(),
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="eco_cup")
dag.create_dag(etl_func=_transfer)
