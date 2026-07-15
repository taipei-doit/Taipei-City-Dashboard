#!/usr/bin/env python3
"""Split a nationwide Taiwan GTFS feed into bus / rail / train sub-feeds for the
transit-isochrone backend (app/services/isochrone).

Output layout matches gtfs.LoadFeed():
    <out>/{bus,rail,train}/{stops,routes,trips,stop_times,
                            shapes,calendar,calendar_dates,frequencies}.txt

This is the preprocessing PR #1291 referenced as data/scripts/app.py but left
out. The mode split is purely by route_type; the "jumpfrog" express-bus feed is
derived in Go from the bus feed (gtfs.SplitJumpfrog), so it is NOT emitted here.

Usage:
    python gtfs_split.py --src /path/gtfs.zip --out /opt/gtfs
    python gtfs_split.py --src /path/gtfs.zip --out /opt/gtfs --bbox none   # nationwide
    python gtfs_split.py --selftest
"""
import argparse
import os
import shutil
import sys
import tempfile
import zipfile
from collections import defaultdict

import pandas as pd

# route_type -> sub-feed. Taiwan TDX uses standard codes here: 1=metro/LRT,
# 2=rail (HSR/TRA), 3=bus. 4=ferry and 1102=air are dropped (no BE feed).
ROUTE_TYPE_MODE = {"0": "rail", "1": "rail", "2": "train", "3": "bus"}
MODES = ("bus", "rail", "train")

# ponytail: bbox region filter (min_lat, min_lon, max_lat, max_lon) covering
# 雙北 (Taipei + New Taipei). A route is kept whole if any of its stops falls
# inside. Swap for admin-polygon point-in-poly only if exact municipal edges
# ever matter — a bbox is plenty for isochrone reachability.
TAIPEI_BBOX = (24.6, 121.2, 25.35, 122.1)

# The 8 files LoadFeed() reads. Headers used only as fallback when the source
# omits an optional file (BE errors if any are missing).
FILES = ("stops", "routes", "trips", "stop_times",
         "shapes", "calendar", "calendar_dates", "frequencies")
FALLBACK_HEADER = {
    "shapes": "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence",
    "calendar": "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date",
    "calendar_dates": "service_id,date,exception_type",
    "frequencies": "trip_id,start_time,end_time,headway_secs",
}
CHUNK = 500_000  # rows per chunk for the two streamed big files


class Source:
    """Read GTFS .txt files from a zip or a directory, transparently."""

    def __init__(self, path):
        self.path = path
        self.zf = zipfile.ZipFile(path) if zipfile.is_zipfile(path) else None

    def has(self, name):
        if self.zf is not None:
            return (name + ".txt") in self.zf.namelist()
        return os.path.exists(os.path.join(self.path, name + ".txt"))

    def _open(self, name):
        fn = name + ".txt"
        return self.zf.open(fn) if self.zf is not None else open(os.path.join(self.path, fn), "rb")

    def read(self, name, **kw):
        # dtype=str + na_filter=False: keep IDs/times verbatim, never invent NaN.
        return pd.read_csv(self._open(name), dtype=str, na_filter=False,
                           encoding="utf-8-sig", **kw)

    def chunks(self, name):
        return self.read(name, chunksize=CHUNK)


def _write(out, mode, name, df):
    df.to_csv(os.path.join(out, mode, name + ".txt"), index=False, encoding="utf-8")


def split(src, out, bbox=TAIPEI_BBOX):
    s = Source(src)
    for m in MODES:
        os.makedirs(os.path.join(out, m), exist_ok=True)

    # 1. routes -> mode (drop ferry/air and anything unmapped)
    routes = s.read("routes")
    routes["__mode"] = routes["route_type"].map(ROUTE_TYPE_MODE)
    routes = routes[routes["__mode"].notna()].copy()
    route_mode = dict(zip(routes["route_id"], routes["__mode"]))

    # 2. trips of those routes
    trips = s.read("trips")
    trips = trips[trips["route_id"].isin(route_mode)].copy()
    has_shape = "shape_id" in trips.columns
    trip_route = dict(zip(trips["trip_id"], trips["route_id"]))
    trip_service = dict(zip(trips["trip_id"], trips["service_id"]))
    trip_shape = dict(zip(trips["trip_id"], trips["shape_id"])) if has_shape else {}

    # 3. stops -> in-bbox set + parent map
    stops = s.read("stops")
    stop_parent = dict(zip(stops["stop_id"], stops.get("parent_station", pd.Series("", index=stops.index))))
    if bbox is None:
        kept_routes = set(route_mode)
    else:
        lat = pd.to_numeric(stops["stop_lat"], errors="coerce")
        lon = pd.to_numeric(stops["stop_lon"], errors="coerce")
        in_box = (lat >= bbox[0]) & (lon >= bbox[1]) & (lat <= bbox[2]) & (lon <= bbox[3])
        in_bbox_stops = set(stops.loc[in_box, "stop_id"])
        # 4. pass A over stop_times: routes that touch the bbox
        kept_routes = set()
        for ch in s.chunks("stop_times"):
            hit = ch.loc[ch["stop_id"].isin(in_bbox_stops), "trip_id"]
            kept_routes.update(trip_route[t] for t in hit.unique() if t in trip_route)

    # 5. derive kept sets (keep whole routes -> internally consistent sub-feeds)
    trip_mode = {t: route_mode[r] for t, r in trip_route.items() if r in kept_routes}
    kept_trips = set(trip_mode)
    shape_mode = {}
    service_modes = defaultdict(set)
    for t in kept_trips:
        m = trip_mode[t]
        service_modes[trip_service[t]].add(m)
        sh = trip_shape.get(t, "")
        if sh:
            shape_mode[sh] = m

    # 6. pass B over stop_times: write per mode, collect used stops
    st_cols = list(s.read("stop_times", nrows=0).columns)
    st_w = {m: open(os.path.join(out, m, "stop_times.txt"), "w", encoding="utf-8", newline="") for m in MODES}
    for m in MODES:
        pd.DataFrame(columns=st_cols).to_csv(st_w[m], index=False)
    used_stops = {m: set() for m in MODES}
    for ch in s.chunks("stop_times"):
        ch = ch[ch["trip_id"].isin(kept_trips)]
        if ch.empty:
            continue
        mser = ch["trip_id"].map(trip_mode)
        for m in MODES:
            sub = ch[mser == m]
            if not sub.empty:
                sub[st_cols].to_csv(st_w[m], header=False, index=False)
                used_stops[m].update(sub["stop_id"])
    for w in st_w.values():
        w.close()

    # 7. stops per mode, with parent-station closure (transfers/coords need it)
    for m in MODES:
        keep = set(used_stops[m])
        frontier = set(keep)
        while frontier:
            nxt = {stop_parent.get(x, "") for x in frontier}
            nxt = {p for p in nxt if p and p not in keep}
            keep |= nxt
            frontier = nxt
        _write(out, m, "stops", stops[stops["stop_id"].isin(keep)])

    # 8. routes / trips / calendar / calendar_dates / frequencies (in-memory)
    for m in MODES:
        _write(out, m, "routes",
               routes[(routes["__mode"] == m) & routes["route_id"].isin(kept_routes)].drop(columns="__mode"))
        tt = trips[trips["trip_id"].isin(kept_trips)]
        _write(out, m, "trips", tt[tt["trip_id"].map(trip_mode) == m])

    for name in ("calendar", "calendar_dates"):
        if not s.has(name):
            for m in MODES:
                _write_header(out, m, name)
            continue
        df = s.read(name)
        for m in MODES:
            svc = {sid for sid, ms in service_modes.items() if m in ms}
            _write(out, m, name, df[df["service_id"].isin(svc)])

    if s.has("frequencies"):
        fq = s.read("frequencies")
        fq = fq[fq["trip_id"].isin(kept_trips)]
        for m in MODES:
            _write(out, m, "frequencies", fq[fq["trip_id"].map(trip_mode) == m])
    else:
        for m in MODES:
            _write_header(out, m, "frequencies")

    # shapes (streamed big file), partitioned by the shape's mode
    if s.has("shapes") and shape_mode:
        sh_cols = list(s.read("shapes", nrows=0).columns)
        sh_w = {m: open(os.path.join(out, m, "shapes.txt"), "w", encoding="utf-8", newline="") for m in MODES}
        for m in MODES:
            pd.DataFrame(columns=sh_cols).to_csv(sh_w[m], index=False)
        for ch in s.chunks("shapes"):
            mser = ch["shape_id"].map(shape_mode)
            for m in MODES:
                sub = ch[mser == m]
                if not sub.empty:
                    sub[sh_cols].to_csv(sh_w[m], header=False, index=False)
        for w in sh_w.values():
            w.close()
    else:
        for m in MODES:
            _write_header(out, m, "shapes")

    counts = {m: sum(1 for _ in open(os.path.join(out, m, "trips.txt"))) - 1 for m in MODES}
    print(f"done -> {out}  trips per feed: {counts}")
    empty = [m for m, n in counts.items() if n == 0]
    if empty:
        # Caught exactly this: TDX V3/Map/GTFS/Static ships metro (捷運) route
        # definitions but no trips, so the `rail` feed comes out empty. Metro
        # schedules must be supplied from a separate GTFS source and merged in.
        print(f"WARNING: feed(s) {empty} have 0 trips — source has routes but no "
              f"schedules for these modes; supply them from another GTFS.", file=sys.stderr)
    return counts


def build(main_src, out, metro_src=None, bbox=TAIPEI_BBOX):
    """Assemble the final {bus,rail,train} tree the BE reads: bus + train from
    the national feed (V3/Map/GTFS/Static), rail (metro) from the TRTC feed
    (V3/Map/GTFS/Static/Rail/TRTC). TDX only publishes metro GTFS for TRTC
    ("目前只提供北捷"), so one metro source covers rail — no multi-operator
    merge / id-namespacing needed.

    ponytail: if TDX ever adds more metro operators, prefix each operator's ids
    and concat into rail/ instead of this straight copy (ids would collide).
    """
    split(main_src, out, bbox=bbox)  # -> bus + train (rail comes out empty)
    if metro_src:
        tmp = tempfile.mkdtemp()
        try:
            split(metro_src, tmp, bbox=bbox)  # -> rail (its bus/train are empty)
            rail = os.path.join(out, "rail")
            shutil.rmtree(rail)
            shutil.copytree(os.path.join(tmp, "rail"), rail)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print(f"merged metro rail -> {out}/rail")


def _write_header(out, mode, name):
    with open(os.path.join(out, mode, name + ".txt"), "w", encoding="utf-8") as f:
        f.write(FALLBACK_HEADER[name] + "\n")


def _selftest():
    import tempfile

    src = tempfile.mkdtemp()
    out = tempfile.mkdtemp()

    def w(name, text):
        with open(os.path.join(src, name + ".txt"), "w", encoding="utf-8") as f:
            f.write(text)

    # R_BUS touches bbox (S_IN); R_FAR only out-of-bbox -> dropped; R_RAIL kept.
    w("routes", "route_id,route_type\nR_BUS,3\nR_RAIL,1\nR_FAR,3\nR_FERRY,4\n")
    w("trips", "route_id,trip_id,service_id,shape_id\n"
               "R_BUS,T_BUS,SVC1,SH1\nR_RAIL,T_RAIL,SVC2,\nR_FAR,T_FAR,SVC1,\n")
    w("stops", "stop_id,stop_name,stop_lat,stop_lon,parent_station\n"
               "S_IN,in,25.0,121.5,S_PARENT\nS_PARENT,parent,25.01,121.51,\n"
               "S_OUT,out,23.0,120.0,\nS_RAIL,rail,25.05,121.55,\n")
    w("stop_times", "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
                    "T_BUS,08:00:00,08:00:00,S_IN,1\nT_RAIL,09:00:00,09:00:00,S_RAIL,1\n"
                    "T_FAR,07:00:00,07:00:00,S_OUT,1\n")
    w("shapes", "shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence\nSH1,25.0,121.5,1\nSH9,23.0,120.0,1\n")
    w("calendar", "service_id,monday,start_date,end_date\nSVC1,1,20260101,20261231\nSVC2,1,20260101,20261231\n")
    w("calendar_dates", "service_id,date,exception_type\nSVC1,20260101,1\n")
    w("frequencies", "trip_id,start_time,end_time,headway_secs\nT_BUS,08:00:00,20:00:00,600\n")

    split(src, out, bbox=TAIPEI_BBOX)

    def rows(m, name):
        return pd.read_csv(os.path.join(out, m, name + ".txt"), dtype=str, na_filter=False)

    # all 8 files exist per mode
    for m in MODES:
        for name in FILES:
            assert os.path.exists(os.path.join(out, m, name + ".txt")), f"missing {m}/{name}"

    bus_routes = set(rows("bus", "routes")["route_id"])
    assert bus_routes == {"R_BUS"}, f"region filter failed: {bus_routes}"  # R_FAR dropped, R_FERRY dropped
    assert set(rows("rail", "routes")["route_id"]) == {"R_RAIL"}
    assert rows("train", "routes").empty  # no route_type=2 in fixture

    # referential integrity: every stop_times.stop_id is in stops
    bus_stops = set(rows("bus", "stops")["stop_id"])
    bus_st_stops = set(rows("bus", "stop_times")["stop_id"])
    assert bus_st_stops <= bus_stops, "dangling stop_id in stop_times"
    # parent-station closure pulled S_PARENT in even though no trip stops there
    assert "S_PARENT" in bus_stops, "parent closure failed"
    # shape only for the bus trip; SH9 (unused) excluded
    assert set(rows("bus", "shapes")["shape_id"]) == {"SH1"}
    # calendar partitioned by the mode that uses the service
    assert set(rows("bus", "calendar")["service_id"]) == {"SVC1"}
    assert set(rows("rail", "calendar")["service_id"]) == {"SVC2"}
    print("selftest OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", help="nationwide GTFS .zip or directory (bus + train)")
    ap.add_argument("--metro", help="TRTC metro GTFS .zip or directory (fills the rail feed)")
    ap.add_argument("--out", help="output dir (gets bus/ rail/ train/ subdirs)")
    ap.add_argument("--bbox", default="taipei", help='"taipei" (default) or "none" for nationwide')
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    bbox = None if a.bbox == "none" else TAIPEI_BBOX
    if a.selftest:
        _selftest()
    elif a.src and a.out:
        build(a.src, a.out, metro_src=a.metro, bbox=bbox)
    else:
        ap.error("need --src and --out (or --selftest)")
