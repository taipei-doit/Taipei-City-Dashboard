import json

from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import create_engine
from sqlalchemy.sql import text as sa_text

from utils.get_time import get_tpe_now_time
from utils.llm_provider import generate_text

AI_SUMMARY_TABLE = "component_ai_summary"

CHART_SYSTEM_PROMPT = (
    "你是台北市城市儀表板的資料助理。請根據提供的組件資訊,用繁體中文寫一段"
    "100 到 150 字的摘要,說明這個圖表組件的用途、代表的指標意義,以及使用者可以如何解讀這份資料。"
    "只需輸出摘要內容,不要條列、不要加標題。"
)

MAP_SYSTEM_PROMPT = (
    "你是台北市城市儀表板的資料助理。請根據提供的地圖圖層資訊,用繁體中文寫一段"
    "100 到 150 字的摘要,說明這個圖層呈現的空間資料內容、欄位意義,以及使用者可以從地圖上觀察到什麼。"
    "只需輸出摘要內容,不要條列、不要加標題。"
)


def fetch_enabled_components(engine):
    sql = sa_text(
        """
        SELECT index, city, short_desc, long_desc, use_case
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
            }
            for row in conn.execute(sql).fetchall()
        ]


def fetch_map_configs(engine, index, city):
    """依 createTempComponentDB 同樣的 join 邏輯:query_charts.map_config_ids -> component_maps.id"""
    sql = sa_text(
        """
        SELECT cm.index, cm.title, cm.type, cm.property
        FROM query_charts qc
        JOIN unnest(qc.map_config_ids) AS id_value ON true
        JOIN component_maps cm ON cm.id = id_value
        WHERE qc.index = :index AND qc.city = :city
        """
    )
    with engine.connect() as conn:
        return [
            {"map_index": row[0], "title": row[1], "type": row[2], "property": row[3]}
            for row in conn.execute(sql, {"index": index, "city": city}).fetchall()
        ]


def fetch_sql_view_info(catalog_engine, geodata_engine, view_name):
    """
    圖層在 GeoServer 分兩種:
    1. SQL View(JDBC_VIRTUAL_TABLE):真正的查詢語法(可能是 join/聚合)存在 GeoServer 自己的
       catalog(pgconfig.resourceinfo.info.metadata.MetadataMap.JDBC_VIRTUAL_TABLE...sql),
       不是 dashboard-stream 裡的實體物件,要先查這裡。
    2. 純資料表:GeoServer 直接對應 dashboard-stream 的一張表,沒有 JDBC_VIRTUAL_TABLE,
       退回查 information_schema.columns 拿欄位清單。
    兩邊都查不到就回 None,讓上層優雅跳過。
    """
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
                sql_query = vt.get("sql")
                if sql_query:
                    return {"sql_query": sql_query.strip(), "columns": None}
        except Exception as e:
            print(f"GeoServer catalog lookup failed for {view_name}: {e}")

    if geodata_engine is None:
        return None

    columns_sql = sa_text(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = :view_name
        ORDER BY ordinal_position
        """
    )
    with geodata_engine.connect() as conn:
        columns = [row[0] for row in conn.execute(columns_sql, {"view_name": view_name}).fetchall()]

    if not columns:
        return None
    return {"sql_query": None, "columns": columns}


def build_chart_prompt(component):
    return (
        f"組件名稱(index):{component['index']}\n"
        f"簡短說明:{component['short_desc'] or '無'}\n"
        f"詳細說明:{component['long_desc'] or '無'}\n"
        f"應用情境:{component['use_case'] or '無'}\n"
    )


def build_map_prompt(component, map_rows, sql_view_infos):
    lines = [f"組件名稱(index):{component['index']}"]
    for row in map_rows:
        lines.append(f"\n圖層:{row['title']}(類型:{row['type']})")

        # property 是 PG json 欄位,psycopg2 可能已自動解成 list,也可能是原始字串,兩種都要接
        raw_property = row["property"]
        if isinstance(raw_property, str):
            try:
                fields = json.loads(raw_property)
            except ValueError:
                fields = []
        else:
            fields = raw_property or []
        if fields:
            field_desc = "、".join(
                f"{f.get('name')}({f.get('key')})" for f in fields if isinstance(f, dict)
            )
            lines.append(f"欄位說明:{field_desc}")

        view_info = sql_view_infos.get(row["map_index"])
        if view_info:
            if view_info["sql_query"]:
                lines.append(f"圖層 SQL 查詢邏輯:{view_info['sql_query']}")
            elif view_info["columns"]:
                lines.append(f"資料庫欄位:{'、'.join(view_info['columns'])}")

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
# public(實測這個部署唯一的 PostGIS store 就是指向它)。所以 catalog 用原本連線,geodata 借
# 用同一組帳密把 dbname 換掉即可,不用另外設 connection。之後如果 GeoServer 掛了不只一個
# store,要改成真的走 pgconfig.storeinfo 查每個 layer 對應的 store db,而不是寫死。
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

    components = fetch_enabled_components(engine)
    print(f"Found {len(components)} components with enable_ai_summary = true.")

    for component in components:
        index, city = component["index"], component["city"]

        try:
            chart_summary = generate_text(CHART_SYSTEM_PROMPT, build_chart_prompt(component))
            write_summary(engine, index, city, "chart", chart_summary)
            print(f"[{index}/{city}] chart summary written.")
        except Exception as e:
            print(f"[{index}/{city}] chart summary failed: {e}")

        map_rows = fetch_map_configs(engine, index, city)
        if not map_rows:
            continue

        sql_view_infos = {}
        if catalog_engine is not None or geodata_engine is not None:
            for row in map_rows:
                try:
                    info = fetch_sql_view_info(catalog_engine, geodata_engine, row["map_index"])
                    if info:
                        sql_view_infos[row["map_index"]] = info
                except Exception as e:
                    print(f"[{index}/{city}] SQL view lookup failed for {row['map_index']}: {e}")

        try:
            map_prompt = build_map_prompt(component, map_rows, sql_view_infos)
            map_summary = generate_text(MAP_SYSTEM_PROMPT, map_prompt)
            write_summary(engine, index, city, "map", map_summary)
            print(f"[{index}/{city}] map summary written.")
        except Exception as e:
            print(f"[{index}/{city}] map summary failed: {e}")
