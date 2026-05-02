from airflow import DAG
from operators.common_pipeline import CommonDag


PDF_URL = "https://www-ws.gov.taipei/Download.ashx?u=LzAwMS9VcGxvYWQvMzA2L3JlbGZpbGUvNDQ3NzYvNzY1MTI5NC9iODNhOTkwZC02M2IyLTQ0ZDItYmNlOS1lN2U0YjQ3ZDc0YzgucGRm&n=MTE1MDTpo7LmsLTlj7DmsLTos6rmqqLpqZfntZDmnpwucGRm&icon=.pdf"
STANDARD_MPN_PER_100ML = 6


def _roc_datetime(date_text, time_text):
    from datetime import datetime
    import pandas as pd
    import pytz

    year, month, day = [int(part) for part in date_text.split("/")]
    hour, minute = [int(part) for part in time_text.split(":")]
    dt = datetime(year + 1911, month, day, hour, minute)
    return pd.Timestamp(pytz.timezone("Asia/Taipei").localize(dt))


def _numeric_result(value_text):
    return float(value_text.replace("<", ""))


def _extract_words_from_pdf(pdf_path):
    import fitz

    pages = []
    doc = fitz.open(pdf_path)
    for page_number, page in enumerate(doc, start=1):
        words = []
        for word in page.get_text("words"):
            x0, y0, _x1, _y1, text, *_ = word
            words.append(
                {
                    "text": text.strip(),
                    "x": float(x0),
                    "y": float(y0),
                }
            )
        pages.append((page_number, words))
    return pages


def _parse_quality_pdf(pdf_path):
    import re
    import pandas as pd

    name_pattern = re.compile(r"^(?P<sample_name>.+)\((?P<fountain_id>[0-9A-Za-z]+)\)$")
    date_pattern = re.compile(r"^\d{3}/\d{2}/\d{2}$")
    time_pattern = re.compile(r"^\d{2}:\d{2}$")
    value_pattern = re.compile(r"^<?\d+(\.\d+)?$")
    rows = []

    for page_number, words in _extract_words_from_pdf(pdf_path):
        names = []
        dates = []
        times = []
        values = []

        for word in words:
            text = word["text"]
            name_match = name_pattern.match(text)
            if name_match and word["x"] < 280:
                names.append(
                    {
                        "sample_name": name_match.group("sample_name").strip(),
                        "fountain_id": name_match.group("fountain_id").strip(),
                        "y": word["y"],
                    }
                )
            elif date_pattern.match(text):
                dates.append(word)
            elif time_pattern.match(text):
                times.append(word)
            elif word["x"] > 440 and value_pattern.match(text):
                values.append(word)

        for name in names:
            # Each sample name is vertically centered across its test rows.
            candidate_dates = [
                date for date in dates if name["y"] - 24 <= date["y"] <= name["y"] + 36
            ]
            for date in candidate_dates:
                time = min(times, key=lambda item: abs(item["y"] - date["y"]), default=None)
                value = min(values, key=lambda item: abs(item["y"] - date["y"]), default=None)
                if (
                    time is None
                    or value is None
                    or abs(time["y"] - date["y"]) > 3
                    or abs(value["y"] - date["y"]) > 3
                ):
                    continue
                rows.append(
                    {
                        "sample_name": name["sample_name"],
                        "fountain_id": name["fountain_id"],
                        "sampled_at": _roc_datetime(date["text"], time["text"]),
                        "sample_date": date["text"],
                        "sample_time": time["text"],
                        "e_coli_result": value["text"],
                        "e_coli_numeric": _numeric_result(value["text"]),
                        "e_coli_unit": "MPN/100mL",
                        "standard_mpn_per_100ml": STANDARD_MPN_PER_100ML,
                        "quality_status": (
                            "合格"
                            if _numeric_result(value["text"]) <= STANDARD_MPN_PER_100ML
                            else "不合格"
                        ),
                        "source_page": page_number,
                    }
                )

    data = pd.DataFrame(rows).drop_duplicates(
        subset=["fountain_id", "sampled_at", "e_coli_result"]
    )
    if data.empty:
        raise ValueError("No quality test rows parsed from PDF.")
    return data.sort_values(["fountain_id", "sampled_at"])


def _create_joined_views(engine):
    from sqlalchemy.sql import text as sa_text

    sql = """
        CREATE OR REPLACE VIEW public.drinking_fountain_with_quality AS
        SELECT
            df.*,
            qt.sample_name AS quality_sample_name,
            qt.sampled_at AS latest_quality_sampled_at,
            qt.e_coli_result AS latest_e_coli_result,
            qt.e_coli_numeric AS latest_e_coli_numeric,
            qt.e_coli_unit AS latest_e_coli_unit,
            qt.standard_mpn_per_100ml,
            COALESCE(qt.quality_status, '未檢驗') AS quality_status,
            qt.source_page AS quality_source_page
        FROM public.drinking_fountain df
        LEFT JOIN public.drinking_fountain_quality_test qt
            ON lower(df.fountain_id) = lower(qt.fountain_id);

        CREATE OR REPLACE VIEW public.drinking_fountain_with_quality_taipei AS
        SELECT *
        FROM public.drinking_fountain_with_quality
        WHERE city = '臺北市';
    """
    with engine.begin() as conn:
        conn.execute(sa_text(sql))


def _transfer(**kwargs):
    import tempfile
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from sqlalchemy.sql import text as sa_text
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import update_lasttime_in_data_to_dataset_info

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    response = requests.get(PDF_URL, proxies=proxies, timeout=90)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
        pdf_file.write(response.content)
        pdf_file.flush()
        parsed_data = _parse_quality_pdf(pdf_file.name)

    parsed_data["data_time"] = get_tpe_now_time_str()
    latest_data = (
        parsed_data.sort_values("sampled_at")
        .groupby("fountain_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    columns = [
        "data_time",
        "sample_name",
        "fountain_id",
        "sampled_at",
        "sample_date",
        "sample_time",
        "e_coli_result",
        "e_coli_numeric",
        "e_coli_unit",
        "standard_mpn_per_100ml",
        "quality_status",
        "source_page",
    ]

    engine = create_engine(ready_data_db_uri)
    if load_behavior != "current+history":
        raise ValueError("drinking_fountain_quality_test expects current+history load_behavior.")

    with engine.begin() as conn:
        conn.execute(sa_text(f"TRUNCATE TABLE {default_table}"))
        latest_data[columns].to_sql(
            default_table, conn, if_exists="append", index=False, schema="public"
        )
        parsed_data[columns].to_sql(
            history_table, conn, if_exists="append", index=False, schema="public"
        )

    _create_joined_views(engine)

    update_lasttime_in_data_to_dataset_info(
        engine,
        airflow_dag_id=dag_id,
        lasttime_in_data=str(parsed_data["sampled_at"].max()),
    )


dag = CommonDag(
    proj_folder="proj_city_dashboard", dag_folder="drinking_fountain_quality_test"
)
dag.create_dag(etl_func=_transfer)
