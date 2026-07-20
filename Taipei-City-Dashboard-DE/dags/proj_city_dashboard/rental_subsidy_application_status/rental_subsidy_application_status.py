from airflow import DAG
from operators.common_pipeline import CommonDag


def _ensure_ready_table(engine, table_name, col_map):
    from utils.ready_table_schema import ensure_ready_table

    ensure_ready_table(
        engine,
        table_name,
        col_map,
        {
            "縣市": "city",
            "項目": "year",
            "租金補貼申請戶數": "application_households",
            "租金補貼計畫戶數": "planned_households",
            "租金補貼核定戶數": "approved_households",
        },
    )


def _rental_subsidy_application_status(**kwargs):
    import re

    import pandas as pd
    from sqlalchemy import create_engine
    from utils.extract_stage import get_current_rid_from_page_id, get_data_taipei_api
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    COL_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "city": 'character varying(10) COLLATE pg_catalog."default"',
        "year": "integer",
        "application_households": "integer",
        "planned_households": "integer",
        "approved_households": "integer",
    }
    SELECT_COLUMNS = list(COL_MAP.keys())

    TAIPEI_PAGE_ID = "6297943a-1e71-480d-967c-635855df66fe"

    def _to_ad_year(value):
        year = pd.to_numeric(
            pd.Series(value, dtype="string").str.extract(r"(\d+)", expand=False),
            errors="coerce",
        )
        return year.mask(year < 1911, year + 1911).astype("Int64")

    def _to_int(series):
        return pd.to_numeric(
            series.astype("string").str.replace(",", "", regex=False),
            errors="coerce",
        ).astype("Int64")

    data_time = pd.to_datetime("now").strftime("%Y-%m-%d %H:%M:%S+08")

    # === Extract ===
    taipei_rid = get_current_rid_from_page_id(TAIPEI_PAGE_ID)
    taipei_raw = pd.DataFrame(get_data_taipei_api(taipei_rid))

    # === Transform: Taipei ===
    data = taipei_raw.rename(
        columns={
            "項目": "year",
            "租金補貼申請戶數": "application_households",
            "租金補貼計畫戶數": "planned_households",
            "租金補貼核定戶數": "approved_households",
        }
    )
    # 來源自 112 年度起將兩個年度合併為一筆(如「112-113年度」),數值為兩年合計,
    # 計畫戶數僅寫「見備註」。依備註「申請戶數計N戶，核准戶數計N戶」的合計數字
    # 平分拆回逐年(餘數給後一年,兩年加總不變)。
    # ponytail: 備註僅有兩年合計、無逐年官方數,平分為近似值;若來源日後改回
    # 逐年列(如「112年度」),不會命中此 regex,會原樣通過。
    # 自 111 年度起租金補貼改由中央三百億方案受理,無臺北市計畫戶數,故留空。
    combo = data["year"].astype("string").str.extract(r"^(\d+)-(\d+)年度$")
    combo_mask = combo[0].notna()
    split_rows = []
    for idx in data.index[combo_mask]:
        y1, y2 = int(combo.loc[idx, 0]), int(combo.loc[idx, 1])
        m = re.search(
            r"申請戶數計([\d,]+)戶，核准戶數計([\d,]+)戶", str(data.loc[idx, "備註"])
        )
        if y2 != y1 + 1 or not m:
            continue  # 拆不出來寧可整筆略過,也不寫入錯的數字
        applied, approved = (int(g.replace(",", "")) for g in m.groups())
        for year, app, appr in (
            (y1, applied // 2, approved // 2),
            (y2, applied - applied // 2, approved - approved // 2),
        ):
            split_rows.append(
                {
                    "year": f"{year}年度",
                    "application_households": app,
                    "planned_households": None,
                    "approved_households": appr,
                }
            )
    data = pd.concat([data[~combo_mask], pd.DataFrame(split_rows)], ignore_index=True)
    data["city"] = "臺北市"
    data["year"] = _to_ad_year(data["year"])
    data = data[data["year"].notna()]

    # === Normalize ===
    for col in ["application_households", "planned_households", "approved_households"]:
        data[col] = _to_int(data[col])
    data["data_time"] = data_time
    data = data.sort_values("year").reset_index(drop=True)
    data = data[SELECT_COLUMNS]

    # === Load ===
    engine = create_engine(ready_data_db_uri)
    _ensure_ready_table(engine, default_table, COL_MAP)
    save_dataframe_to_postgresql(
        engine,
        data=data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(engine, dag_id, data["data_time"].max())


dag = CommonDag(
    proj_folder="proj_city_dashboard",
    dag_folder="rental_subsidy_application_status",
)
dag.create_dag(etl_func=_rental_subsidy_application_status)
