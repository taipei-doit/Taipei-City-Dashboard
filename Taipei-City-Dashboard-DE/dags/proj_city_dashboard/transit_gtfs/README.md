# transit_gtfs

雙北大眾運輸 GTFS ingestion for the **transit-isochrone backend** (PR #1291,
`app/services/isochrone`). Schedule: `30 22 5,26 * *` (每月 5、26 日 22:30).

## Flow

```
TDX V3/Map/GTFS/Static            ─┐  download (TDXAuth, Airflow Variables)
TDX V3/Map/GTFS/Static/Rail/TRTC  ─┘
        │  gtfs_split.build():  篩雙北 + 按 route_type 切
        ▼
   bus  (route_type 3)      train (route_type 2 = 台鐵+高鐵)     rail (TRTC 北捷)
        │  每 feed 的 .txt 壓成一個 zip
        ▼
   gtfs_bundle(feed PK, archive bytea, updated_at)   ← 1 表 3 列 (migration 20260625)
```

Only TRTC ships metro GTFS from TDX (others → 400「目前只提供北捷」). 台鐵 included.
`gtfs_split.py` runs standalone too: `python gtfs_split.py --selftest`.

## Backend contract (lives on the isochrone branch, not here)

The BE currently does `gtfs.LoadFeed(GTFSDir+"/"+feed)` reading `.txt` files. To
consume the blob instead, replace the file loader with a zip-blob loader:

```go
// SELECT archive FROM gtfs_bundle WHERE feed = $1   ->  blob []byte
func LoadFeedFromZip(blob []byte, prefix string) (*Feed, error) {
    zr, _ := zip.NewReader(bytes.NewReader(blob), int64(len(blob)))
    // map path.Base(f.Name) -> f; parseStops/parseTrips/... take an io.Reader
    // (refactor openCSV(path) -> csv reader from f.Open()); rest is unchanged.
}
```

`transit.InitService()` then loads `bus`/`rail`/`train` from `gtfs_bundle` rather
than from `global.GTFSDir`. RAPTOR / isochrone code is untouched. Refresh data =
re-run this DAG, then roll the backend so it reloads.
