import json

from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import create_engine
from sqlalchemy.sql import text as sa_text

from utils.get_time import get_tpe_now_time
from utils.llm_provider import generate_text

AI_SUMMARY_TABLE = "component_ai_summary"

# ponytail: 照抄 BE app/util/common.go GetTime() 沒帶參數時的預設值(1990-01-01 ~ 現在,
# 等於全部資料),讓 query_chart 裡的 %s 時間區間代入跟前端預設行為一致。
DEFAULT_TIME_FROM = "1990-01-01T00:00:00+08:00"
ROW_SAMPLE_LIMIT = 20
CELL_TRUNCATE_LEN = 150
QUERY_TIMEOUT_MS = 30000

CHART_SYSTEM_PROMPT = (
    "你是台北市城市儀表板的資料分析助理。請根據提供的組件資訊與圖表資料，"
    "使用繁體中文撰寫一段 150 到 220 字的分析摘要。"
    "摘要應先簡要說明圖表的用途與指標意義，再分析資料中值得關注的趨勢、"
    "高低差異、排名、變化幅度、異常值、轉折點或群組差異，"
    "並說明這些現象可能代表的城市治理意義或使用者可以如何解讀。"
    "請優先引用資料中的具體期間、分類、區域與數值，使洞察具有依據。"
    "若資料不足以判斷原因，只能描述觀察到的現象，不可自行推測因果關係；"
    "若資料沒有明顯趨勢或差異，應如實說明資料分布相對穩定。"
    "只需輸出一段完整摘要，不要條列、不要加標題、不要描述分析步驟。"
)

MAP_SYSTEM_PROMPT = (
    "你是台北市城市儀表板的空間資料分析助理。請根據提供的地圖圖層資訊、"
    "欄位說明與實際圖層資料，使用繁體中文撰寫一段 150 到 220 字的分析摘要。"
    "摘要應先簡要說明圖層呈現的空間資料內容與主要欄位意義；"
    "若提供了地圖顏色/樣式對照，也要說明不同顏色或樣式在地圖上分別代表什麼分類或狀態。"
    "再分析地圖中值得關注的空間分布現象，例如集中區域、稀疏區域、"
    "群聚、熱點、區域差異、鄰近關係、覆蓋範圍或異常點位，"
    "並說明使用者可以如何解讀這些空間特徵及其可能的城市治理意義。"
    "請優先引用資料中的行政區、地點、分類、數量或指標數值，使洞察具有依據。"
    "不得僅依點位數量直接推論事件風險或需求程度，也不可在資料不足時推測因果關係；"
    "若無法辨識明顯空間特徵，應如實說明目前分布較為平均或資訊不足。"
    "只需輸出一段完整摘要，不要條列、不要加標題、不要描述分析步驟。"
)


def fetch_enabled_components(engine):
    sql = sa_text(
        """
        SELECT index, city, short_desc, long_desc, use_case, query_chart
        FROM query_charts
        WHERE enable_ai_summary IS TRUE
        """
    )
    with engine.connect() as conn:
        return [
            {
                "index": row[0],
                "city": row[1],
                "short_desc": row[2],
                "long_desc": row[3],
                "use_case": row[4],
                "query_chart": row[5],
            }
            for row in conn.execute(sql).fetchall()
        ]


def fetch_component_by_index(engine, index, city=None):
    """手動 trigger 帶 index(+選填 city)參數時用,只重新生成指定的組件,不管 enable_ai_summary。"""
    conditions = "index = :index"
    params = {"index": index}
    if city:
        conditions += " AND city = :city"
        params["city"] = city

    sql = sa_text(
        f"""
        SELECT index, city, short_desc, long_desc, use_case, query_chart
        FROM query_charts
        WHERE {conditions}
        """
    )
    with engine.connect() as conn:
        return [
            {
                "index": row[0],
                "city": row[1],
                "short_desc": row[2],
                "long_desc": row[3],
                "use_case": row[4],
                "query_chart": row[5],
            }
            for row in conn.execute(sql, params).fetchall()
        ]


def fetch_map_configs(engine, index, city):
    """依 createTempComponentDB 同樣的 join 邏輯:query_charts.map_config_ids -> component_maps.id"""
    sql = sa_text(
        """
        SELECT cm.index, cm.title, cm.type, cm.property, cm.paint
        FROM query_charts qc
        JOIN unnest(qc.map_config_ids) AS id_value ON true
        JOIN component_maps cm ON cm.id = id_value
        WHERE qc.index = :index AND qc.city = :city
        """
    )
    with engine.connect() as conn:
        return [
            {
                "map_index": row[0],
                "title": row[1],
                "type": row[2],
                "property": row[3],
                "paint": row[4],
            }
            for row in conn.execute(sql, {"index": index, "city": city}).fetchall()
        ]


def _parse_json_field(raw):
    """component_maps 的 json 欄位,psycopg2 可能已自動解成 dict/list,也可能是原始字串,兩種都要接。"""
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except ValueError:
            return None
    return raw


# ponytail: 顏色名稱只是為了讓摘要好讀(LLM 不會自己把 hex 轉成顏色名,只會照抄色碼),
# 用簡單 RGB 歐氏距離配最接近的常見色名即可,不追求色彩學上的精確(例如不做感知均勻空間轉換)。
_NAMED_COLORS = {
    "紅色": (255, 0, 0),
    "深紅色": (139, 0, 0),
    "橙色": (255, 165, 0),
    "黃色": (255, 255, 0),
    "淺綠色": (144, 238, 144),
    "綠色": (0, 128, 0),
    "深綠色": (0, 100, 0),
    "青色": (0, 128, 128),
    "天藍色": (135, 206, 235),
    "藍色": (0, 0, 255),
    "深藍色": (0, 0, 139),
    "靛色": (75, 0, 130),
    "紫色": (128, 0, 128),
    "粉紅色": (255, 192, 203),
    "洋紅色": (255, 0, 255),
    "棕色": (165, 42, 42),
    "米色": (245, 245, 220),
    "黑色": (0, 0, 0),
    "深灰色": (64, 64, 64),
    "灰色": (128, 128, 128),
    "淺灰色": (211, 211, 211),
    "白色": (255, 255, 255),
}


def _is_hex_color(value):
    return (
        isinstance(value, str)
        and len(value) == 7
        and value[0] == "#"
        and all(c in "0123456789abcdefABCDEF" for c in value[1:])
    )


def _hex_to_color_name(hex_color):
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    name, _ = min(
        _NAMED_COLORS.items(),
        key=lambda item: (item[1][0] - r) ** 2 + (item[1][1] - g) ** 2 + (item[1][2] - b) ** 2,
    )
    return name


def _color_label(value):
    """paint 表達式裡的值是 hex 色碼就換成最接近的中文顏色名(不要把色碼原樣丟給 LLM,
    它只會照抄,不會自己翻譯);不是色碼(例如已經是分類標籤字串)就原樣輸出。"""
    return _hex_to_color_name(value) if _is_hex_color(value) else str(value)


def describe_paint(paint):
    """
    把 component_maps.paint(Mapbox/MapLibre style 的著色表達式)轉成人看得懂的顏色對照
    說明給 LLM。只特別處理最常見的 match 表達式(依欄位值對應顏色 + 預設色),其他複雜
    表達式(interpolate/case/巢狀...)就把原始值丟給 LLM 自己解讀,不刻意寫完整的
    expression parser。
    """
    paint = _parse_json_field(paint)
    if not paint or not isinstance(paint, dict):
        return None

    lines = []
    for prop_name, value in paint.items():
        if isinstance(value, list) and len(value) >= 2 and value[0] == "match":
            get_expr = value[1]
            field = get_expr[1] if isinstance(get_expr, list) and len(get_expr) > 1 else str(get_expr)
            rest = value[2:]
            if len(rest) % 2 == 1:
                default, pairs = rest[-1], rest[:-1]
            else:
                default, pairs = None, rest
            mapping = "、".join(
                f"{pairs[i]}={_color_label(pairs[i + 1])}" for i in range(0, len(pairs), 2)
            )
            desc = f"{prop_name} 依欄位「{field}」的值決定:{mapping}"
            if default is not None:
                desc += f",其他值預設為 {_color_label(default)}"
            lines.append(desc)
        elif isinstance(value, str):
            lines.append(f"{prop_name} 固定為 {_color_label(value)}")
        else:
            lines.append(f"{prop_name}: {json.dumps(value, ensure_ascii=False)}")

    return "；".join(lines) if lines else None


def _default_time_to():
    return get_tpe_now_time(is_with_tz=True).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def run_query_sample(engine, query, limit=ROW_SAMPLE_LIMIT):
    """
    真的執行一段 SQL,只抓前 limit 筆當樣本回傳給 LLM,不把整包資料塞進 prompt。
    照抄 BE(componentData.go)的邏輯:query 裡剛好有 2 個 %s 才代入 time_from/time_to。

    ponytail: fetchmany(limit) 在預設 psycopg2 設定下不是真的 server-side cursor,不能完全
    避免整包結果先進到 client 端記憶體;這裡另外加 statement_timeout 當安全網,擋住失控的慢查詢。
    這些 query_chart 本來就是給前端即時渲染圖表用的正式查詢,預期已經是合理範圍,如果之後真的
    遇到會回傳超大結果集的 query,再改用 server-side cursor。
    """
    if query.count("%s") == 2:
        query = query % (DEFAULT_TIME_FROM, _default_time_to())

    with engine.begin() as conn:
        conn.execute(sa_text(f"SET LOCAL statement_timeout = {QUERY_TIMEOUT_MS}"))
        result = conn.execute(sa_text(query))
        if not result.returns_rows:
            return {"columns": [], "rows": [], "total_rows": 0}
        columns = list(result.keys())
        rows = [list(r) for r in result.fetchmany(limit)]

    # 總筆數是額外的佐證資訊,用獨立連線/transaction 查,失敗就算了不影響已經拿到的樣本。
    total_rows = None
    try:
        stripped = query.strip().rstrip(";")
        with engine.begin() as conn:
            conn.execute(sa_text(f"SET LOCAL statement_timeout = {QUERY_TIMEOUT_MS}"))
            total_rows = conn.execute(sa_text(f"SELECT COUNT(*) FROM ({stripped}) AS _sub")).scalar()
    except Exception as e:
        print(f"total row count failed (non-fatal): {e}")

    return {"columns": columns, "rows": rows, "total_rows": total_rows}


def _truncate(value, limit=CELL_TRUNCATE_LEN):
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "…"


def format_query_result(query, result):
    lines = [f"實際查詢語法:\n{query.strip()}"]
    if result and result["rows"]:
        total = result.get("total_rows")
        sample_count = len(result["rows"])
        if total is not None and total > sample_count:
            lines.append(f"\n查詢結果總筆數:{total}(以下為前 {sample_count} 筆樣本)")
        else:
            lines.append(f"\n查詢結果總筆數:{total if total is not None else sample_count}")
        lines.append(f"欄位:{', '.join(result['columns'])}")
        lines.append("樣本內容:")
        for row in result["rows"]:
            lines.append("  " + " | ".join(_truncate(v) for v in row))
    else:
        lines.append("\n查詢結果:無資料")
    return "\n".join(lines)


def fetch_map_query_info(catalog_engine, geodata_engine, view_name):
    """
    圖層在 GeoServer 分兩種:
    1. SQL View(JDBC_VIRTUAL_TABLE):真正的查詢語法(可能是 join/聚合)存在 GeoServer 自己的
       catalog(pgconfig.resourceinfo.info.metadata.MetadataMap.JDBC_VIRTUAL_TABLE...sql),
       不是 dashboard-stream 裡的實體物件,要先查這裡拿語法。
    2. 純資料表:GeoServer 直接對應 dashboard-stream 的一張表,沒有 JDBC_VIRTUAL_TABLE,
       退回組一個 SELECT * FROM 該表當查詢語法。
    兩種情況都會真的執行這段查詢,回傳語法 + 樣本結果給上層組 prompt。查不到就回 None。
    """
    sql_query = None
    if catalog_engine is not None:
        try:
            with catalog_engine.connect() as conn:
                row = conn.execute(
                    sa_text("SELECT info FROM pgconfig.resourceinfo WHERE name = :name"),
                    {"name": view_name},
                ).fetchone()
            if row and row[0]:
                vt = (
                    row[0].get("metadata", {})
                    .get("MetadataMap", {})
                    .get("JDBC_VIRTUAL_TABLE", {})
                    .get("Literal", {})
                    .get("value", {})
                )
                candidate = vt.get("sql")
                if candidate:
                    sql_query = candidate.strip()
        except Exception as e:
            print(f"GeoServer catalog lookup failed for {view_name}: {e}")

    if geodata_engine is None:
        return None

    if sql_query is None:
        with geodata_engine.connect() as conn:
            exists = conn.execute(
                sa_text("SELECT 1 FROM information_schema.tables WHERE table_name = :view_name"),
                {"view_name": view_name},
            ).fetchone()
        if not exists:
            return None
        sql_query = f'SELECT * FROM "{view_name}"'

    try:
        result = run_query_sample(geodata_engine, sql_query)
    except Exception as e:
        print(f"query execution failed for {view_name}: {e}")
        result = None

    return {"sql_query": sql_query, "result": result}


def build_chart_prompt(component, query_result):
    lines = [
        f"組件名稱(index):{component['index']}",
        f"簡短說明:{component['short_desc'] or '無'}",
        f"詳細說明:{component['long_desc'] or '無'}",
        f"應用情境:{component['use_case'] or '無'}",
    ]
    if component["query_chart"]:
        lines.append("")
        lines.append(format_query_result(component["query_chart"], query_result))
    return "\n".join(lines)


def build_map_prompt(component, map_rows, map_query_infos):
    lines = [f"組件名稱(index):{component['index']}"]
    for row in map_rows:
        lines.append(f"\n圖層:{row['title']}(類型:{row['type']})")

        fields = _parse_json_field(row["property"]) or []
        if fields:
            field_desc = "、".join(
                f"{f.get('name')}({f.get('key')})" for f in fields if isinstance(f, dict)
            )
            lines.append(f"欄位說明:{field_desc}")

        paint_desc = describe_paint(row["paint"])
        if paint_desc:
            lines.append(f"地圖顏色/樣式對照:{paint_desc}")

        query_info = map_query_infos.get(row["map_index"])
        if query_info:
            lines.append(format_query_result(query_info["sql_query"], query_info["result"]))

    return "\n".join(lines)


def write_summary(engine, index, city, summary_type, result):
    now = get_tpe_now_time(is_with_tz=True)
    sql = sa_text(
        f"""
        INSERT INTO {AI_SUMMARY_TABLE} (index, city, type, result, created_at, updated_at)
        VALUES (:index, :city, :type, :result, :now, :now)
        """
    )
    with engine.begin() as conn:
        conn.execute(
            sql,
            {"index": index, "city": city, "type": summary_type, "result": result, "now": now},
        )


# ponytail: geoserver-postgres 接的 db(geoserver_pgconfig)是 GeoServer 自己的 pgconfig
# catalog(workspace/layer/store 設定 + SQL View 查詢語法都存在這裡的 jsonb 欄位)。實際圖層
# 資料表(非 SQL View 的 fallback 用)則在同一台 Postgres 的 dashboard-stream db、schema
# public(實測這個部署唯一的 PostGIS store 就是指向它,也是 BE query_chart 實際查詢的 db)。
# 所以 catalog 用原本連線,geodata 借用同一組帳密把 dbname 換掉即可,不用另外設 connection。
# 之後如果 GeoServer 掛了不只一個 store,要改成真的走 pgconfig.storeinfo 查每個 layer 對應
# 的 store db,而不是寫死。
GEODATA_DBNAME = "dashboard-stream"


def _get_geoserver_catalog_engine():
    try:
        return create_engine(PostgresHook(postgres_conn_id="geoserver-postgres").get_uri())
    except Exception as e:
        print(f"geoserver-postgres connection not available, skip GeoServer catalog lookup: {e}")
        return None


def _get_geodata_engine():
    try:
        conn = PostgresHook(postgres_conn_id="geoserver-postgres").get_connection("geoserver-postgres")
        uri = f"postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{GEODATA_DBNAME}"
        return create_engine(uri)
    except Exception as e:
        print(f"geoserver-postgres connection not available, skip geodata table lookup: {e}")
        return None


def ai_summary_etl(**kwargs):
    dashboard_uri = PostgresHook(postgres_conn_id="dashboard-postgre").get_uri()
    engine = create_engine(dashboard_uri)
    catalog_engine = _get_geoserver_catalog_engine()
    geodata_engine = _get_geodata_engine()

    # 手動 trigger 帶 conf(index/city/type)時,只重新生成指定的組件,不管 enable_ai_summary、
    # 也不跑其他組件。city/type 沒帶就是「該 index 底下所有 city」「chart 跟 map 都跑」。
    dag_run = kwargs.get("dag_run")
    conf = dag_run.conf if dag_run and dag_run.conf else {}
    target_index = conf.get("index")
    target_type = conf.get("type")

    if target_type not in (None, "chart", "map"):
        raise ValueError(f"conf.type 只能是 'chart' 或 'map',收到: {target_type!r}")

    if target_index:
        components = fetch_component_by_index(engine, target_index, conf.get("city"))
        print(
            f"手動指定重新生成 index={target_index} city={conf.get('city') or '(全部 city)'} "
            f"type={target_type or '(chart+map)'},找到 {len(components)} 筆。"
        )
        if not components:
            print(f"query_charts 裡查無 index={target_index} city={conf.get('city')},略過。")
    else:
        components = fetch_enabled_components(engine)
        print(f"Found {len(components)} components with enable_ai_summary = true.")

    do_chart = target_type in (None, "chart")
    do_map = target_type in (None, "map")

    for component in components:
        index, city = component["index"], component["city"]

        if do_chart:
            try:
                query_result = None
                if component["query_chart"] and geodata_engine is not None:
                    try:
                        query_result = run_query_sample(geodata_engine, component["query_chart"])
                    except Exception as e:
                        print(f"[{index}/{city}] query_chart execution failed: {e}")

                chart_summary = generate_text(CHART_SYSTEM_PROMPT, build_chart_prompt(component, query_result))
                write_summary(engine, index, city, "chart", chart_summary)
                print(f"[{index}/{city}] chart summary written.")
            except Exception as e:
                print(f"[{index}/{city}] chart summary failed: {e}")

        if not do_map:
            continue

        map_rows = fetch_map_configs(engine, index, city)
        if not map_rows:
            continue

        map_query_infos = {}
        if catalog_engine is not None or geodata_engine is not None:
            for row in map_rows:
                try:
                    info = fetch_map_query_info(catalog_engine, geodata_engine, row["map_index"])
                    if info:
                        map_query_infos[row["map_index"]] = info
                except Exception as e:
                    print(f"[{index}/{city}] map query lookup failed for {row['map_index']}: {e}")

        try:
            map_prompt = build_map_prompt(component, map_rows, map_query_infos)
            map_summary = generate_text(MAP_SYSTEM_PROMPT, map_prompt)
            write_summary(engine, index, city, "map", map_summary)
            print(f"[{index}/{city}] map summary written.")
        except Exception as e:
            print(f"[{index}/{city}] map summary failed: {e}")
