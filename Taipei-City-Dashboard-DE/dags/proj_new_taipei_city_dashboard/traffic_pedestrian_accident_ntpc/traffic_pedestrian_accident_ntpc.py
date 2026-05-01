from airflow import DAG
from operators.common_pipeline import CommonDag


def etl_function(**kwargs):
    import io
    import zipfile
    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    # 警政署每年封存的傷亡道路交通事故資料（全國，含新北市）
    # ROC 111-114 年 → CE 2022-2025
    YEAR_URLS = {
        2022: "https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/E52FB959-55BD-4D31-892C-21C87041FC87/resource/28128A43-4F80-4670-8F61-30F959477218/download",
        2023: "https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/E68DFD97-92B3-4A78-A447-87F1390B54B0/resource/C0876EEB-9468-4B23-8E67-AB57E3563A1B/download",
        2024: "https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/CCAD7AA8-5139-4066-8BE3-D6CC3154C137/resource/36C1D864-51F8-4A78-9D68-8298E00B0732/download",
        2025: "https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/FCD9C2D4-CB71-4EAA-AA4C-B088E5FE3157/resource/90BFBDAC-BA7E-4255-B557-EED2ED77AA93/download",
    }

    # Extract – 逐年下載並標記西元年
    all_dfs = []
    for ce_year, url in YEAR_URLS.items():
        print(f"Downloading {ce_year}...")
        try:
            resp = requests.get(url, timeout=300)
            resp.raise_for_status()
        except Exception as e:
            print(f"  Warning: {ce_year} download failed: {e}")
            continue

        try:
            z = zipfile.ZipFile(io.BytesIO(resp.content))
            csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
            for csv_f in csv_files:
                for enc in ("utf-8-sig", "big5", "cp950", "utf-8"):
                    try:
                        df_part = pd.read_csv(z.open(csv_f), encoding=enc, low_memory=False)
                        df_part["_ce_year"] = ce_year
                        all_dfs.append(df_part)
                        print(f"  {csv_f}: {len(df_part)} rows")
                        break
                    except (UnicodeDecodeError, Exception):
                        continue
        except zipfile.BadZipFile:
            for enc in ("utf-8-sig", "big5", "utf-8"):
                try:
                    df_part = pd.read_csv(io.StringIO(resp.content.decode(enc)), low_memory=False)
                    df_part["_ce_year"] = ce_year
                    all_dfs.append(df_part)
                    break
                except Exception:
                    continue

    if not all_dfs:
        raise RuntimeError("No NTPC data downloaded")

    raw_data = pd.concat(all_dfs, ignore_index=True)
    print(f"Total rows before filter: {len(raw_data)}")

    # Transform
    # 1. 篩選新北市
    city_col = next(
        (c for c in raw_data.columns if "警局層" in c or "處理單位" in c), None
    )
    if city_col:
        data = raw_data[raw_data[city_col].str.contains("新北市", na=False)].copy()
    else:
        data = raw_data.copy()
        print("Warning: city column not found, skipping city filter")

    # 2. 篩選行人
    ped_col = next(
        (c for c in data.columns if "行動狀態大類" in c or "行動狀態" in c), None
    )
    if ped_col:
        # 全國 A2 資料：大類「人的狀態」= 行人/路人（相對於「車的狀態」= 駕駛/乘客）
        data = data[
            data[ped_col].str.contains("人的狀態|行人", na=False)
        ].copy()
    else:
        print("Warning: pedestrian column not found, skipping pedestrian filter")

    print(f"NTPC pedestrian rows: {len(data)}")

    # 3. 解析小時（HHMMSS 整數，例如 102012 → 10、40100 → 4）
    time_col = next((c for c in data.columns if "發生時間" in c), None)
    if time_col:
        data["hour"] = (
            pd.to_numeric(data[time_col], errors="coerce")
            .fillna(0).astype(int) // 10000
        )
    else:
        data["hour"] = 0

    # 4. 解析年度與月份（直接用 URL 對應的西元年，不依賴 CSV 的民國年欄位）
    data["year"] = data["_ce_year"].astype(int)
    month_col = next((c for c in data.columns if "發生月份" in c or ("發生月" in c and "份" in c)), None)
    data["month"] = pd.to_numeric(data[month_col], errors="coerce").fillna(0).astype(int) if month_col else 0

    # 5. 解析死傷人數（格式如 "0死1傷"）
    casualty_col = next((c for c in data.columns if "死亡受傷" in c), None)
    if casualty_col:
        data["death_count"] = (
            data[casualty_col].astype(str).str.extract(r"(\d+)死")[0]
            .fillna(0).astype(int)
        )
        data["injury_count"] = (
            data[casualty_col].astype(str).str.extract(r"(\d+)傷")[0]
            .fillna(0).astype(int)
        )
    else:
        data["death_count"] = 0
        data["injury_count"] = 0

    # 6. 其他欄位
    age_col = next((c for c in data.columns if "年齡" in c), None)
    cause_col = next((c for c in data.columns if "肇因" in c and "個別" in c), None)
    ped_sub_col = next((c for c in data.columns if "行動狀態子" in c), None)

    data["age"] = pd.to_numeric(data[age_col], errors="coerce").fillna(0).astype(int) if age_col else 0
    data["cause_name"] = data[cause_col].fillna("其他") if cause_col else "其他"
    data["pedestrian_action"] = data[ped_sub_col].fillna("") if ped_sub_col else ""

    # 7. 座標
    lng_col = next((c for c in data.columns if "經度" in c or c.lower() in ["lng", "lon"]), None)
    lat_col = next((c for c in data.columns if "緯度" in c or c.lower() in ["lat"]), None)
    data["lng"] = pd.to_numeric(data[lng_col], errors="coerce") if lng_col else None
    data["lat"] = pd.to_numeric(data[lat_col], errors="coerce") if lat_col else None

    # 8. 過濾異常座標（新北市範圍）
    data = data[
        data["lng"].notna() & data["lat"].notna() &
        data["lng"].between(121.3, 122.0) &
        data["lat"].between(24.8, 25.3)
    ]
    # 排除已知錯誤定位（新北市政府座標，被橋梁事故誤用）
    data = data[
        ~(data["lng"].between(121.455, 121.475) & data["lat"].between(25.005, 25.020))
    ]
    print(f"Rows after coordinate filter: {len(data)}")

    # 9. 加入 data_time 與 geometry
    now_str = str(pd.Timestamp.now(tz="Asia/Taipei"))
    data["data_time"] = convert_str_to_time_format(pd.Series([now_str] * len(data)))

    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data["lng"], y=data["lat"], from_crs=4326
    )

    ready_data = gdata[[
        "data_time", "year", "month", "hour",
        "death_count", "injury_count", "age",
        "cause_name", "pedestrian_action", "lng", "lat", "wkb_geometry"
    ]]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point",
    )
    lasttime_in_data = ready_data["data_time"].max()
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=str(lasttime_in_data)
    )


dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="traffic_pedestrian_accident_ntpc"
)
dag.create_dag(etl_func=etl_function)
