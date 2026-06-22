from airflow import DAG
from operators.common_pipeline import CommonDag


def _urban_planning_new_tpe(**kwargs):
    import pandas as pd
    import geopandas as gpd
    from sqlalchemy import create_engine, text as sa_text
    from shapely.geometry import MultiPolygon
    from shapely.validation import make_valid
    from utils.extract_stage import (
        NewTaipeiAPIClient,
        get_current_rid_from_page_id,
        get_shp_file,
    )
    from utils.transform_geometry import convert_geometry_to_wkbgeometry
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    GEOMETRY_TYPE = "MultiPolygon"

    DATASET_ID = "fe26e0a5-54c2-4876-bbc7-150243c048f5"
    TAIPEI_PAGE_ID = "3bab0a01-7936-4218-8cb5-f74dfcb43dda"
    TAIPEI_FALLBACK_RID = "10196e7d-2460-4b8a-b1d2-84001d09d7a4"
    FALLBACK_ZONE_URL = "https://urban.planning.ntpc.gov.tw/opendataDownload/新北市使用分區.zip"
    DISTRICT_URL = (
        "https://www.tgos.tw/tgos/VirtualDir/Product/"
        "3fe61d4a-ca23-4f45-8aca-4a536f40f290/"
        "%E9%84%89%28%E9%8E%AE%E3%80%81%E5%B8%82%E3%80%81%E5%8D%80%29"
        "%E7%95%8C%E7%B7%9A1140318.zip"
    )

    ZONE_MERGE_MAP = {
        "住宅區": "住宅區",
        "商業區": "商業產業用地",
        "市場倉儲用地": "商業產業用地",
        "特定專用區": "商業產業用地",
        "工業區": "工業區",
        "交通用地": "交通運輸用地",
        "停車場用地": "交通運輸用地",
        "港埠漁港用地": "交通運輸用地",
        "公園綠地廣場用地": "綠地保育遊憩用地",
        "保護區": "綠地保育遊憩用地",
        "保存區": "綠地保育遊憩用地",
        "風景遊憩區": "綠地保育遊憩用地",
        "農業區": "綠地保育遊憩用地",
        "非都市土地": "綠地保育遊憩用地",
        "河川水利用地": "水利防災用地",
        "護坡防災用地": "水利防災用地",
        "文教學校用地": "文教體育用地",
        "體育運動用地": "文教體育用地",
        "機關公共設施用地": "公共服務設施用地",
        "公用事業用地": "公共服務設施用地",
        "醫療社福用地": "公共服務設施用地",
        "環保設施用地": "公共服務設施用地",
        "宗教殯葬用地": "公共服務設施用地",
        "軍事用地": "公共服務設施用地",
        "計畫範圍": "計畫範圍",
        "未分類": "未分類",
    }

    def _standardize_zone(zone):
        if pd.isna(zone) or not str(zone).strip():
            return "未分類"
        name = str(zone).replace(" ", "").replace("　", "")
        if "非都市" in name:
            return "非都市土地"
        if "細部計畫範圍" in name or "規劃範圍" in name:
            return "計畫範圍"
        if any(k in name for k in ["學校", "國小", "國中", "國民小學", "小學", "高中", "高職", "中學", "商職", "工專", "師專", "大學", "大專", "學院", "海專", "文教", "文中", "文小", "文高", "文專", "社教", "博物館", "藝術", "文化", "電影", "視聽", "教育", "中正紀念堂"]):
            return "文教學校用地"
        if any(k in name for k in ["國家公園", "風景", "鳳景", "景觀", "遊憩", "遊樂", "休閒", "休憩", "娛樂", "露營", "野營", "野餐", "海水浴場", "海濱浴場", "濱海", "海洋遊樂", "戲水", "高爾夫", "動物園", "國民旅舍"]):
            return "風景遊憩區"
        if "住宅" in name or "別墅" in name or name == "住":
            return "住宅區"
        if "商業" in name or name in {"商", "中心商業區", "建成商業區", "鄰里商業區", "海濱商業區", "景觀商業區"}:
            return "商業區"
        if "工業" in name or name in {"工", "零星工業區"}:
            return "工業區"
        if "農業" in name or name in {"農", "農會專用區"}:
            return "農業區"
        if "保存" in name or "古蹟" in name or "遺址" in name or "歷史" in name:
            return "保存區"
        if "保護" in name or "保安" in name or "生態" in name or "水庫保護" in name or "地質" in name:
            return "保護區"
        if any(k in name for k in ["公園", "綠地", "綠化", "綠園道", "綠帶", "廣場", "兒童遊", "公(兒)", "園道", "帶狀公園", "鄰里公園", "植物園"]):
            return "公園綠地廣場用地"
        if any(k in name for k in ["道路", "人行", "交通", "高速公路", "快速道路", "快速公路", "鐵路", "高速鐵路", "捷運", "車站", "轉運", "隧道", "橋樑", "公路車站", "公車站", "調度站", "園道用地", "過水道路", "機場"]):
            return "交通用地"
        if any(k in name for k in ["河川", "河道", "行水", "水域", "水道", "溝渠", "水溝", "排水", "下水道", "堤防", "滯洪", "調節池", "蓄水池", "防洪", "沉砂池", "海堤", "水利", "灌溉", "抽水站", "水庫"]):
            return "河川水利用地"
        if any(k in name for k in ["機關", "行政", "司法", "警察", "消防", "公共服務", "公共事業", "公用事業", "社區中心", "服務中心", "青年活動"]):
            return "機關公共設施用地"
        if any(k in name for k in ["電力", "電路鐵塔", "鐵塔", "變電", "電信", "通訊", "郵政", "自來水", "瓦斯", "煤氣", "天然氣", "能源", "核能", "核電", "發電", "水產養殖", "轉接站"]):
            return "公用事業用地"
        if any(k in name for k in ["市場", "批發", "零售", "倉儲", "臨時賣店"]):
            return "市場倉儲用地"
        if "停車" in name:
            return "停車場用地"
        if any(k in name for k in ["體育", "運動"]):
            return "體育運動用地"
        if "護坡" in name or "擋土牆" in name:
            return "護坡防災用地"
        if any(k in name for k in ["醫療", "醫院", "衛生", "衛福", "社會福利", "社福", "安養", "護校"]):
            return "醫療社福用地"
        if any(k in name for k in ["宗教", "寺廟", "墓", "殯", "葬", "納骨"]):
            return "宗教殯葬用地"
        if any(k in name for k in ["軍事", "軍人", "軍"]):
            return "軍事用地"
        if any(k in name for k in ["垃圾", "環保", "污水", "汙水", "焚化", "土石方"]):
            return "環保設施用地"
        if any(k in name for k in ["港埠", "漁港", "遊艇", "碼頭", "遊船", "海域"]):
            return "港埠漁港用地"
        if "已開發建築密集地區" in name:
            return "住宅區"
        if any(k in name for k in ["產業", "科技", "資訊", "工商", "商務", "金融", "旅館", "觀光", "特定專用", "專用區", "開發區", "聯合開發", "水岸發展", "原住民生活", "食品工業研究所"]):
            return "特定專用區"
        if any(k in name for k in ["加油站", "油庫"]):
            return "公用事業用地"
        return "未分類"

    def _first_present_value(row, columns):
        for column in columns:
            if column in row.index and pd.notna(row[column]) and str(row[column]).strip():
                return str(row[column]).strip()
        return ""

    def _build_zone_polygons(urban_gdf, county_name, zone_columns):
        # ponytail: 保留每個來源多邊形(不做行政區 sjoin 拆分),只做分區標準化 + 面積,留 geometry
        urban = urban_gdf[urban_gdf.geometry.notna()].copy()
        urban["geometry"] = urban["geometry"].apply(
            lambda geom: make_valid(geom) if geom is not None and not geom.is_valid else geom
        )
        urban = urban[urban.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
        urban["source_zone"] = urban.apply(
            lambda row: _first_present_value(row, zone_columns),
            axis=1,
        )
        urban["land_use_zone"] = urban["source_zone"].map(_standardize_zone).map(
            lambda value: ZONE_MERGE_MAP.get(value, "未分類")
        )
        urban["county"] = county_name
        # 面積(公頃);輸入為 EPSG:3826(公尺)
        urban["area"] = (urban.geometry.area / 10000).round(2)
        return gpd.GeoDataFrame(
            urban[["county", "source_zone", "land_use_zone", "area", "geometry"]],
            geometry="geometry",
            crs="EPSG:3826",
        )

    # === Extract ===
    try:
        resources = NewTaipeiAPIClient(DATASET_ID).get_data(page=0, size=10)
        ntpc_shp_url = next(
            row["link"] for row in resources if "使用分區" in row.get("name", "")
        )
    except Exception:
        ntpc_shp_url = FALLBACK_ZONE_URL

    try:
        taipei_rid = get_current_rid_from_page_id(
            TAIPEI_PAGE_ID,
            resource_name_contains="全市主計",
        )
    except Exception:
        taipei_rid = TAIPEI_FALLBACK_RID
    taipei_shp_url = (
        "https://data.taipei/api/frontstage/tpeod/dataset/resource.download"
        f"?rid={taipei_rid}"
    )

    raw_taipei_gdf = get_shp_file(
        taipei_shp_url,
        f"{dag_id}_taipei",
        3826,
        encoding="big5",
        file_ends_with="面.shp",
        is_verify=False,
    )
    raw_ntpc_gdf = get_shp_file(
        ntpc_shp_url,
        dag_id,
        3826,
        encoding="big5",
        is_verify=False,
    )

    # === Transform ===
    data = pd.concat(
        [
            _build_zone_polygons(
                raw_taipei_gdf,
                "臺北市",
                ("使用分區", "分區簡稱", "分區代碼"),
            ),
            _build_zone_polygons(raw_ntpc_gdf, "新北市", ("ZONE",)),
        ],
        ignore_index=True,
    )
    data = gpd.GeoDataFrame(data, geometry="geometry", crs="EPSG:3826")
    # 統一成 MultiPolygon(save_geodataframe 要求單一 geometry_type)
    data["geometry"] = data["geometry"].apply(
        lambda geom: geom
        if geom is None or geom.geom_type == "MultiPolygon"
        else MultiPolygon([geom])
    )
    data = data[data.geom_type == "MultiPolygon"].copy()
    data["data_time"] = pd.Timestamp.now(tz="Asia/Taipei")
    # geometry(EPSG:3826) -> wkb_geometry(EPSG:4326)
    data = convert_geometry_to_wkbgeometry(data, from_crs=3826)
    gdata = data.drop(columns=["geometry"])

    # === Load ===
    engine = create_engine(ready_data_db_uri)
    # ponytail: 一次性 count->geo schema 遷移。舊表是 count 欄(無 wkb_geometry),
    # 而 save 的 replace=TRUNCATE+append 需表存在且 schema 相符,故缺 geometry 欄就重建。
    with engine.begin() as conn:
        has_geo = conn.execute(
            sa_text(
                "SELECT count(*) FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=:t "
                "AND column_name='wkb_geometry'"
            ),
            {"t": default_table},
        ).scalar()
        if not has_geo:
            conn.execute(sa_text(f'DROP TABLE IF EXISTS public."{default_table}"'))
            conn.execute(
                sa_text(
                    f'CREATE TABLE public."{default_table}" ('
                    "ogc_fid bigserial PRIMARY KEY, "
                    "data_time timestamp with time zone DEFAULT CURRENT_TIMESTAMP, "
                    "county character varying(10), "
                    "source_zone text, "
                    "land_use_zone character varying(30), "
                    "area double precision, "
                    "wkb_geometry geometry(MultiPolygon, 4326), "
                    "_ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP, "
                    "_mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP)"
                )
            )
    save_geodataframe_to_postgresql(
        engine,
        gdata=gdata,
        load_behavior=load_behavior,
        geometry_type=GEOMETRY_TYPE,
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(engine, dag_id, gdata["data_time"].max())


dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="urban_planning_new_tpe",
)
dag.create_dag(etl_func=_urban_planning_new_tpe)
