from airflow import DAG
from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    import re
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from html import unescape

    import pandas as pd
    import requests
    from sqlalchemy import create_engine
    from utils.get_time import get_tpe_now_time_str
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df

    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")

    base_url = "https://vbs.sports.taipei"
    list_url = f"{base_url}/venues/ajax.php"
    headers = {
        "accept": "*/*",
        "charset": "utf-8",
        "content-type": "application/x-www-form-urlencoded",
        "origin": base_url,
        "referer": f"{base_url}/venues/",
        "user-agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
        ),
    }

    session = requests.Session()
    response = session.post(
        list_url,
        data="FUNC=GetVenues",
        headers=headers,
        proxies=proxies,
        timeout=60,
    )
    response.raise_for_status()
    venues = response.json()
    if not venues:
        raise ValueError("Sports venue API returned no records.")

    def to_abs_url(path):
        if not path:
            return None
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{base_url}{path}"

    def parse_number(value):
        return pd.to_numeric(value, errors="coerce")

    def parse_lat_lng(html):
        html = unescape(html)
        match = re.search(
            r'id=["\']VLatLon["\'][^>]*value=["\']\s*([0-9.]+)\s*,\s*([0-9.]+)',
            html,
        )
        if not match:
            match = re.search(r'center=([0-9.]+),([0-9.]+)', html)
        if not match:
            return None, None
        return float(match.group(1)), float(match.group(2))

    def fetch_detail_row(venue):
        venue_id = str(venue.get("SN") or "").strip()
        if not venue_id:
            return None

        detail_url = f"{base_url}/venues/?K={venue_id}"
        detail_response = requests.get(
            detail_url,
            headers={"referer": f"{base_url}/venues/", "user-agent": headers["user-agent"]},
            proxies=proxies,
            timeout=60,
        )
        detail_response.raise_for_status()
        lat, lng = parse_lat_lng(detail_response.text)
        if lat is None or lng is None:
            return None

        return {
            "data_time": get_tpe_now_time_str(is_with_tz=True),
            "venue_id": venue_id,
            "name": venue.get("Name"),
            "name_eng": venue.get("NameEng"),
            "main_name": venue.get("MainName"),
            "main_name_eng": venue.get("MainNameEng"),
            "district": venue.get("MainArea"),
            "district_eng": venue.get("MainAreaEng"),
            "is_open": venue.get("Open") == "是",
            "is_sports_center": venue.get("SportsCenter") == "是",
            "organ": venue.get("Organ"),
            "people_capacity": parse_number(venue.get("PeopleInC")),
            "area_sqm": parse_number(venue.get("LevelGround")),
            "rental_status": venue.get("RentalStatus"),
            "locker_rent_status": venue.get("LockerRentStatus"),
            "sports_center_rent_url": venue.get("SportsCenterRentUrl"),
            "photo_url": to_abs_url(venue.get("Image")),
            "detail_url": detail_url,
            "lat": lat,
            "lng": lng,
        }

    rows = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(fetch_detail_row, venue) for venue in venues]
        for future in as_completed(futures):
            row = future.result()
            if row:
                rows.append(row)

    if not rows:
        raise ValueError("No sports venue records had parseable coordinates.")

    data = pd.DataFrame(rows)
    gdata = add_point_wkbgeometry_column_to_df(
        data,
        x=data["lng"],
        y=data["lat"],
        from_crs=4326,
    )

    ready_data = gdata[
        [
            "data_time",
            "venue_id",
            "name",
            "name_eng",
            "main_name",
            "main_name_eng",
            "district",
            "district_eng",
            "is_open",
            "is_sports_center",
            "organ",
            "people_capacity",
            "area_sqm",
            "rental_status",
            "locker_rent_status",
            "sports_center_rent_url",
            "photo_url",
            "detail_url",
            "lng",
            "lat",
            "wkb_geometry",
        ]
    ]

    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type="Point",
    )
    update_lasttime_in_data_to_dataset_info(
        engine,
        airflow_dag_id=dag_id,
        lasttime_in_data=get_tpe_now_time_str(is_with_tz=True),
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="sports_venue")
dag.create_dag(etl_func=_transfer)
