from airflow import DAG
from operators.common_pipeline import CommonDag

# 定義 Airflow DAG 要執行的 ETL 任務函式
def _transfer(**kwargs):
    '''
    從 TDX 抓取新北市自行車道資料，解析地理欄位並寫入 PostgreSQL。

    範例資料格式如下：
    {
        "RouteName": "中正國中體育場",
        "AuthorityName": "NULL",
        "CityCode": "NWT",
        "City": "新北市",
        "Town": "土城區",
        "RoadSectionStart": "廣福街68巷",
        "RoadSectionEnd": "金城路二段",
        "Direction": "雙向",
        "CyclingType": "NULL",
        "CyclingLength": 1100,
        "FinishedTime": "960409",
        "UpdateTime": "2025-02-18T00:00:49+08:00",
        "Geometry": "MULTILINESTRING ((121.459078004121 24.9904630035153,121.45913999526))"
    }
    '''
    # 匯入必要的函式與模組
    from utils.extract_stage import get_tdx_data
    from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine
    import geopandas as gpd
    from shapely import wkt    
    import pandas as pd
    from geoalchemy2 import WKTElement

    # 常數設定
    FROM_CRS = 4326  # 使用 WGS84 (經緯度)
    GEOMETRY_TYPE = "MultiLineStringZ"  # 幾何資料型別

    # 從 DAG kwargs 取得外部設定參數（包含 config 檔中的內容）
    ready_data_db_uri = kwargs.get('ready_data_db_uri')  # 目標資料庫 URI
    proxies = kwargs.get('proxies')  # 若使用代理
    dag_infos = kwargs.get('dag_infos')  # job_config.json 的設定資訊

    # 從 dag_infos 中取得必要欄位
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')  # append, replace, merge...
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')

    # 資料來源 API（新北市自行車道）
    NEW_TAIPEI_URL = "https://tdx.transportdata.tw/api/basic/v2/Cycling/Shape/City/NewTaipei?%24&%24format=JSON"

    # 呼叫工具函式取得原始資料，轉為 pandas DataFrame
    raw_data = get_tdx_data(NEW_TAIPEI_URL, output_format='dataframe')
    data = raw_data.copy()

    # 安全地將 Geometry 欄位的字串轉為 shapely 幾何物件
    def safe_load_wkt(x):
        try:
            return wkt.loads(x)
        except Exception as e:
            print(f"Error parsing WKT: {x}, error: {e}")
            return None

    # 將 Geometry 欄位轉為 geometry，濾除無效或格式錯誤資料
    data["geometry"] = data["Geometry"].apply(lambda x: safe_load_wkt(x) if pd.notnull(x) else None)
    data = data[data["geometry"].notnull()]  # 僅保留有效幾何資料

    # 將幾何欄位轉為 WKT 字串再轉回 geometry（確保格式一致）
    data['geometry'] = data['geometry'].apply(lambda geom: geom.wkt if geom is not None else None)
    data['geometry'] = gpd.GeoSeries.from_wkt(data['geometry'])

    # 建立 GeoDataFrame，指定座標系統
    gdata = gpd.GeoDataFrame(data, geometry="geometry", crs=f"EPSG:{FROM_CRS}")

    # 將 geometry 欄位轉為 WKBElement 格式以便儲存進 PostgreSQL/PostGIS
    gdata["wkb_geometry"] = gdata["geometry"].apply(
        lambda x: WKTElement(x.wkt, srid=FROM_CRS) if x is not None else None
    )

    # 新增資料時間欄位供後續更新追蹤
    gdata['data_time'] = gdata['UpdateTime']

    # 重新命名欄位為 snake_case，符合資料庫命名慣例
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

    # 清理空字串，轉為 None
    gdata['finished_time'] = gdata['finished_time'].replace('', None)
    gdata['update_time'] = gdata['update_time'].replace('', None)

    # 移除多餘欄位，保留必要欄位（幾何改用 wkb_geometry）
    gdata = gdata.drop(columns=["geometry", "Geometry"])

    # 複製處理後的資料供儲存使用
    ready_data = gdata.copy()

    # 建立資料庫連線
    engine = create_engine(ready_data_db_uri)

    # 呼叫工具函式將 GeoDataFrame 寫入 PostgreSQL/PostGIS
    save_geodataframe_to_postgresql(
        engine=engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )

    # 抓取最新資料時間，更新資料集紀錄資訊（供前台或後台檢視資料時間用）
    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)

# 建立 DAG 物件，指定專案與 DAG 所在目錄
dag = CommonDag(
    proj_folder='proj_new_taipei_city_dashboard',
    dag_folder='bike_path'
)

# 將 _transfer 函式掛載為 DAG 的主要 ETL 任務
dag.create_dag(etl_func=_transfer)
