import ssl

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from sqlalchemy import create_engine
from urllib3.util.ssl_ import create_urllib3_context

from airflow import DAG
from operators.common_pipeline import CommonDag
from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
from utils.get_time import get_tpe_now_time_str
from utils.transform_geometry import add_point_wkbgeometry_column_to_df


class _LegacyTLSAdapter(HTTPAdapter):
    # data.taipei 憑證缺 Subject Key Identifier,Python 3.13 預設 VERIFY_X509_STRICT 會拒絕,
    # 且 SMOKING_AREA 使用的 API 有時會出現自簽 CA 的 intermediate 憑證,
    # 故同時關閉 strict 旗標 + 停用整個憑證驗證。
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def _make_session():
    session = requests.Session()
    session.mount("https://", _LegacyTLSAdapter())
    return session


def _resolve_rid_from_page(page_id, timeout=30):
    session = _make_session()
    url = f"https://data.taipei/api/frontstage/tpeod/dataset.view?id={page_id}"
    res = session.get(url, timeout=timeout, verify=False)
    res.raise_for_status()
    resources = res.json().get("payload", {}).get("resources", [])
    if not resources:
        raise ValueError(f"No resources found for page_id={page_id}")
    return resources[0]["rid"]


def _fetch_data_taipei(rid, timeout=60):
    session = _make_session()
    base = f"https://data.taipei/api/v1/dataset/{rid}?scope=resourceAquire"
    first = session.get(base, timeout=timeout, verify=False).json()
    count = first["result"]["count"]
    results = []
    for offset in range(0, count + 1, 1000):
        url = f"{base}&offset={offset}&limit=1000"
        page = session.get(url, timeout=timeout, verify=False).json()
        results.extend(page["result"]["results"])
    return results


def _transfer(**kwargs):
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    GEOMETRY_TYPE = 'Point'
    FROM_CRS = 4326

    page_id = "8b2fcdeb-d14b-46c4-92d8-66ad07b96a91"
    rid = _resolve_rid_from_page(page_id)
    res = _fetch_data_taipei(rid)
    raw_data = pd.DataFrame(res)

    raw_data = raw_data.rename(columns={
        '行政區': 'district',
        '地點': 'place_name',
        '地址': 'address',
        '樣態': 'category',
        '開放時間': 'open_time',
        '緯度': 'latitude',
        '經度': 'longitude',
        '相對位置': 'relative_location',
        '照片連結': 'image_url',
        '管理單位': 'management_unit',
        '管理單位電話': 'management_phone',
        '備註': 'remark',
    })

    raw_data['latitude'] = pd.to_numeric(raw_data['latitude'], errors='coerce')
    raw_data['longitude'] = pd.to_numeric(raw_data['longitude'], errors='coerce')

    gdata = add_point_wkbgeometry_column_to_df(
        raw_data,
        raw_data['longitude'],
        raw_data['latitude'],
        from_crs=FROM_CRS,
    )

    # 對齊 DB schema 長度限制,避免 StringDataRightTruncation
    str_limits = {
        'district': 50,
        'place_name': 50,
        'address': 50,
        'category': 50,
        'open_time': 64,
        'relative_location': 50,
        'image_url': 128,
        'management_unit': 50,
        'management_phone': 50,
        'remark': 50,
    }
    for col, limit in str_limits.items():
        gdata[col] = gdata[col].astype(str).str.slice(0, limit)

    ready_data = gdata[[
        'district', 'place_name', 'address', 'category', 'open_time',
        'latitude', 'longitude', 'relative_location', 'image_url',
        'management_unit', 'management_phone', 'remark', 'wkb_geometry',
    ]]

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )

    update_lasttime_in_data_to_dataset_info(
        engine,
        airflow_dag_id=dag_id,
        lasttime_in_data=get_tpe_now_time_str(),
    )


dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='smoking_area').create_dag(etl_func=_transfer)
