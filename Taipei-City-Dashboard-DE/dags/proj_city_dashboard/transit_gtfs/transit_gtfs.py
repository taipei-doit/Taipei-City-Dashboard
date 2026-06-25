from operators.common_pipeline import CommonDag


def _transfer(**kwargs):
    """
    雙北大眾運輸 GTFS for the transit-isochrone backend.

    Downloads two TDX GTFS sources, filters to 雙北 and splits into bus/rail/train,
    then stores each feed as a zipped blob row in `gtfs_bundle` (1 table, 3 rows).
    The backend reads those blobs (LoadFeedFromZip) — see README.md for the contract.

      bus, train  <- V3/Map/GTFS/Static          (route_type 3 / 2 = 台鐵+高鐵)
      rail        <- V3/Map/GTFS/Static/Rail/TRTC (北捷; TDX only ships metro for TRTC)
    """
    import io
    import os
    import shutil
    import tempfile
    import zipfile

    import requests
    from sqlalchemy import LargeBinary, bindparam, create_engine, text

    from proj_city_dashboard.transit_gtfs.gtfs_split import build
    from utils.auth_tdx import TDXAuth
    from utils.load_stage import update_lasttime_in_data_to_dataset_info

    ready_data_db_uri = kwargs["ready_data_db_uri"]
    proxies = kwargs.get("proxies")
    dag_infos = kwargs["dag_infos"]
    dag_id = dag_infos["dag_id"]

    NATIONAL_URL = "https://tdx.transportdata.tw/api/gtfs/V3/Map/GTFS/Static"
    TRTC_URL = "https://tdx.transportdata.tw/api/gtfs/V3/Map/GTFS/Static/Rail/TRTC"

    # Extract: token reuses Airflow Variables TDX_CLIENT_ID/TDX_CLIENT_SECRET (no hardcoded creds)
    token = TDXAuth().get_token(is_proxy=bool(proxies))
    headers = {"authorization": f"Bearer {token}", "accept": "application/octet-stream"}

    work = tempfile.mkdtemp(prefix="transit_gtfs_")
    try:
        national_zip = os.path.join(work, "national.zip")
        trtc_zip = os.path.join(work, "trtc.zip")
        for url, dest in ((NATIONAL_URL, national_zip), (TRTC_URL, trtc_zip)):
            with requests.get(url, headers=headers, proxies=proxies, stream=True, timeout=600) as r:
                r.raise_for_status()
                with open(dest, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        fh.write(chunk)

        # Transform: 雙北 filter + split bus/rail/train (rail from TRTC)
        feeds_dir = os.path.join(work, "feeds")
        build(national_zip, feeds_dir, metro_src=trtc_zip)

        # Load: zip each feed's .txt files and upsert as a blob row
        engine = create_engine(ready_data_db_uri)
        upsert = text(
            "INSERT INTO gtfs_bundle (feed, archive, updated_at) "
            "VALUES (:feed, :archive, NOW()) "
            "ON CONFLICT (feed) DO UPDATE SET archive = EXCLUDED.archive, updated_at = NOW()"
        ).bindparams(bindparam("archive", type_=LargeBinary))
        for feed in ("bus", "rail", "train"):
            feed_dir = os.path.join(feeds_dir, feed)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for name in sorted(os.listdir(feed_dir)):
                    zf.write(os.path.join(feed_dir, name), name)
            data = buf.getvalue()
            with engine.begin() as conn:
                conn.execute(upsert, {"feed": feed, "archive": data})
            print(f"{feed}: wrote {len(data)} bytes to gtfs_bundle")

        update_lasttime_in_data_to_dataset_info(engine, airflow_dag_id=dag_id)
    finally:
        shutil.rmtree(work, ignore_errors=True)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="transit_gtfs")
dag.create_dag(etl_func=_transfer)
