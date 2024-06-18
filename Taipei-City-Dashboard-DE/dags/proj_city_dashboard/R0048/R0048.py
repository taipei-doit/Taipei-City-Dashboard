from airflow import DAG
from operators.common_pipeline import CommonDag
from settings.global_config import PROXIES


def _R0048(**kwargs):
    import json
    import math

    import geopandas as gpd
    import pandas as pd
    from shapely import wkb
    from shapely.ops import substring
    from sqlalchemy import create_engine
    from utils.extract_stage import get_tdx_data
    from utils.load_stage import (
        save_geodataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.transform_time import convert_str_to_time_format

    # Config
    dag_infos = kwargs.get("dag_infos")
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    URL = "https://tdx.transportdata.tw/api/basic/v2/Bus/RealTimeNearStop/City/Taipei?$format=JSON"
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # Extract
    res_json = get_tdx_data(URL)
    for i in res_json:
        i.update({"RouteName_En": i["RouteName"].get("En", None)})
        i.update({"RouteName_Zh_tw": i["RouteName"].get("Zh_tw", None)})
    raw_data = pd.DataFrame(res_json)

    # Transform
    tdx_df = raw_data.copy()
    # rename
    col_map = {
        "PlateNumb": "platenumb",
        "A2EventType": "a2eventtype",
        "BusStatus": "busstatus",
        "Direction": "direction",
        "DutyStatus": "dutystatus",
        "GPSTime": "gpstime",
        "RouteName_En": "routename_en",
        "RouteName_Zh_tw": "routename_zh_tw",
        "SrcUpdateTime": "srcupdatetime",
        "StopSequence": "stopsequence",
        "StopUID": "stopuid",
        "UpdateTime": "updatetime",
        "RouteUID": "routeuid",
    }
    tdx_df = tdx_df.rename(columns=col_map)
    tdx_df = tdx_df[
        [
            "platenumb",
            "routeuid",
            "direction",
            "stopuid",
            "stopsequence",
            "dutystatus",
            "busstatus",
            "a2eventtype",
            "gpstime",
            "srcupdatetime",
            "updatetime",
            "routename_en",
            "routename_zh_tw",
        ]
    ]
    print(tdx_df.shape[0])
    # get other needed data
    engine = create_engine(ready_data_db_uri)
    stop_df = pd.read_sql("SELECT * FROM traffic_bus_stop", con=engine)
    route_df = pd.read_sql("SELECT * FROM tdx_bus_route", con=engine)
    bus_live_df = pd.read_sql("SELECT * FROM tdx_bus_live", con=engine)
    # merge stop_df
    new_tdx = tdx_df.merge(
        stop_df[["routeuid", "fraction", "direction", "stopsequence", "wkb_geometry"]],
        how="inner",
        on=["routeuid", "direction", "stopsequence"],
    )
    new_tdx = new_tdx.rename(
        columns={"wkb_geometry": "wkb_geometry_stop", "fraction": "fraction_stop"}
    )
    print(new_tdx.shape[0])
    print(new_tdx.columns)
    # merge route_df
    new_tdx = new_tdx.merge(
        route_df[["routeuid", "wkb_geometry"]], how="inner", on="routeuid"
    )
    new_tdx = new_tdx.rename(columns={"wkb_geometry": "wkb_geometry_route"})
    print(new_tdx.shape[0])
    print(new_tdx.columns)
    # merge old bus_live_df
    if len(bus_live_df) != 0:
        res = new_tdx.merge(
            bus_live_df[["routeuid", "platenumb", "fraction"]],
            how="left",
            left_on=["routeuid", "platenumb"],
            right_on=["routeuid", "platenumb"],
        )
        res = res.rename(columns={"fraction": "fraction_live"})
        res["fraction_live"] = res["fraction_live"].apply(
            lambda x: float(x) if isinstance(x, float) else float(0)
        )
    else:
        res = new_tdx
        res["fraction_live"] = float(0)
    # get geometry
    res["fraction_stop"] = res["fraction_stop"].apply(
        lambda x: float(x) if isinstance(x, float) else float(0)
    )
    # drop duplicates
    res = res.drop_duplicates(subset=["platenumb"], keep="last")
    # generate linestring from previous point and current point
    res["geometry"] = None
    for i in res.index:
        fraction_live = res["fraction_live"][i]
        fraction_stop = res["fraction_stop"][i]
        # early stop
        if math.isnan(fraction_stop):
            continue
        # adjust invalid fraction_live
        fraction_live_invalid = (math.isnan(fraction_live)) or (
            fraction_live == float(0)
        )
        if fraction_live_invalid:
            fraction_live = fraction_stop
        if fraction_live == fraction_stop:
            fraction_live -= float(0.1)
            if int(res["direction"][i]) == 0:
                fraction_stop += float(0.1)
        # generate linestring
        if (fraction_live > fraction_stop) and (
            abs(fraction_live - fraction_stop) < 0.25
        ):
            res["geometry"][i] = substring(
                wkb.loads(res["wkb_geometry_route"][i], hex=True),
                fraction_live,
                fraction_stop,
                normalized=True,
            )
        elif (fraction_live < fraction_stop) and (
            abs(fraction_live - fraction_stop) < 0.25
        ):
            res["geometry"][i] = substring(
                wkb.loads(res["wkb_geometry_route"][i], hex=True),
                fraction_stop,
                fraction_live,
                normalized=True,
            )
        else:
            if int(res["direction"][i]) == 0:
                res["geometry"][i] = substring(
                    wkb.loads(res["wkb_geometry_route"][i], hex=True),
                    fraction_stop,
                    fraction_live,
                    normalized=True,
                )
            else:
                res["geometry"][i] = substring(
                    wkb.loads(res["wkb_geometry_route"][i], hex=True),
                    fraction_live,
                    fraction_stop,
                    normalized=True,
                )
    # select columns
    data = res[
        [
            "platenumb",
            "routeuid",
            "direction",
            "stopuid",
            "stopsequence",
            "fraction_stop",
            "dutystatus",
            "busstatus",
            "a2eventtype",
            "gpstime",
            "srcupdatetime",
            "updatetime",
            "routename_en",
            "routename_zh_tw",
            "geometry",
        ]
    ]
    # convert geometry to JOSN format for dashboard use
    gdata = gpd.GeoDataFrame(data, crs=f"EPSG:{FROM_CRS}")
    gdata_dict = gdata.to_json()
    res = json.loads(gdata_dict)["features"]
    res_list = []
    for i, value in enumerate(res):
        dict_m = {}
        for k, v in value["properties"].items():
            dict_m[k] = v
        dict_m["geometry"] = str(value["geometry"])
        res_list.append(dict_m)
    final = pd.DataFrame(res_list)
    # reshape
    final = final.rename(columns={"fraction_stop": "fraction"})
    ready_data = final[
        [
            "platenumb",
            "routeuid",
            "direction",
            "stopuid",
            "stopsequence",
            "dutystatus",
            "fraction",
            "busstatus",
            "a2eventtype",
            "gpstime",
            "srcupdatetime",
            "updatetime",
            "routename_en",
            "routename_zh_tw",
            "geometry",
        ]
    ]
    print("======================data columns==========================")
    print(f"======================{final.columns}==========================")

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        geometry_type=GEOMETRY_TYPE,
    )

    # Update dataset_info whether there is new data or not
    engine = create_engine(ready_data_db_uri)

    lasttime_in_data = convert_str_to_time_format(ready_data["updatetime"]).max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="R0048")
dag.create_dag(etl_func=_R0048)
