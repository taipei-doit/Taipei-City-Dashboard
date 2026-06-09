from airflow import DAG
from operators.common_pipeline import CommonDag

# 主 ETL 函式，Airflow DAG 執行時會呼叫這個函式
def _transfer(**kwargs):
    '''
    本段程式主要從 TDX 取得台北市的自行車道幾何資訊，
    並將其轉換為 GeoDataFrame，最後載入到 PostgreSQL 資料庫中。

    範例資料格式如下：
    {
        "RouteName": "三元街(東北側2)",
        "AuthorityName": "NULL",
        "CityCode": "TPE",
        "City": "台北市",
        "Town": "",
        "RoadSectionStart": "和平西路二段104巷",
        "RoadSectionEnd": "和平西路二段98巷",
        "Direction": "雙向",
        "CyclingType": "NULL",
        "CyclingLength": 267,
        "FinishedTime": "1021231",
        "UpdateTime": "2025-02-18T00:01:52+08:00",
        "Geometry": "MULTILINESTRING ((121.507845000865 25.0305410051544, ...))"
    }
    '''
    # 匯入處理函式與套件
    from utils.extract_stage import get_tdx_data
    from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine
    import geopandas as gpd
    from shapely import wkt    
    import pandas as pd
    from geoalchemy2 import WKTElement

    # 從 Airflow 的 context 中取得 DAG 的設定參數
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')  # 如果有使用 proxy
    dag_infos = kwargs.get('dag_infos')

    # 從 DAG 設定中擷取必要資訊
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')

    # TDX API URL：取得台北市的自行車道資料
    TAIPEI_URL = "https://tdx.transportdata.tw/api/basic/v2/Cycling/Shape/City/Taipei?%24&%24format=JSON"
    GEOMETRY_TYPE = "MultiLineStringZ"
    FROM_CRS = 4326  # EPSG:4326 為 WGS84 坐標系統

    # 透過工具函式呼叫 API 並轉為 DataFrame
    raw_data = get_tdx_data(TAIPEI_URL, output_format='dataframe')
    data = raw_data.copy()

    # 定義函式：安全地將字串格式的 WKT 轉換為幾何物件
    def safe_load_wkt(x):
        try:
            return wkt.loads(x)
        except Exception as e:
            print(f"Error parsing WKT: {x}, error: {e}")
            return None

    # 將 Geometry 欄位轉為 geometry 物件，並移除解析失敗的列
    data["geometry"] = data["Geometry"].apply(lambda x: safe_load_wkt(x) if pd.notnull(x) else None)
    data = data[data["geometry"].notnull()]  # 濾掉無效 geometry

    # 將 geometry 物件轉為文字 WKT，接著轉回幾何以建立 GeoDataFrame
    data['geometry'] = data['geometry'].apply(lambda geom: geom.wkt if geom is not None else None)
    data['geometry'] = gpd.GeoSeries.from_wkt(data['geometry'])

    # 建立 GeoDataFrame，並設定座標系統為 EPSG:4326
    gdata = gpd.GeoDataFrame(data, geometry="geometry", crs=f"EPSG:{FROM_CRS}")

    # 加入新的欄位 `wkb_geometry`，用於儲存至 PostgreSQL/PostGIS
    gdata["wkb_geometry"] = gdata["geometry"].apply(
        lambda x: WKTElement(x.wkt, srid=FROM_CRS) if x is not None else None
    )

    # 新增欄位，用於追蹤資料的時間
    gdata['data_time'] = gdata['UpdateTime']

    # 欄位重新命名，轉為 snake_case，方便資料庫儲存
    gdata = gdata.rename(columns={
        "RouteName": "route_name",
        "AuthorityName": "authority_name",
        "CityCode": "city_code",
        "City": "city",
        "Town": "town",
        "RoadSectionStart": "road_section_start",
        "RoadSectionEnd": "road_section_end",
        "Direction": "direction",
        "CyclingType": "cycling_type",
        "CyclingLength": "cycling_length",
        "FinishedTime": "finished_time",
        "UpdateTime": "update_time",
    })

    # 清除空字串並替換為 None
    gdata['finished_time'] = gdata['finished_time'].replace('', None)
    gdata['update_time'] = gdata['update_time'].replace('', None)

    # 移除原始 geometry 欄位（避免重複），只保留 wkb_geometry
    gdata = gdata.drop(columns=["geometry", "Geometry"])
    ready_data = gdata.copy()

    # 建立資料庫連線引擎
    engine = create_engine(ready_data_db_uri)

    # 將處理後的資料寫入 PostgreSQL/PostGIS
    save_geodataframe_to_postgresql(
        engine=engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )

    # 取得資料中最新的更新時間，寫回 metadata 表做紀錄
    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


# 建立 DAG 實例，指定專案與 DAG 所屬資料夾
dag = CommonDag(
    proj_folder='proj_city_dashboard',
    dag_folder='bike_path'
)

# 將 _transfer 函式掛載至 DAG 中，作為 ETL 執行邏輯
dag.create_dag(etl_func=_transfer)
