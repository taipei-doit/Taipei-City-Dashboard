# 後端接入規格(不需每月重建、零停機)

## 資料在哪

dashboard-stream 的 `gtfs_bundle` 表,3 列:

```
 feed  │ archive (bytea)                  │ updated_at
 bus   │ bus feed 的 8 個 .txt 壓成 zip   │ 2026-06-25 10:47:50
 rail  │ rail(北捷)的 .txt 壓成 zip        │ 2026-06-25 10:47:50  ← 同一個 transaction,時間一致
 train │ train(台鐵+高鐵)的 .txt 壓成 zip  │ 2026-06-25 10:47:50
```

每月 5、26 日 DAG 自動更新。`updated_at` 三列一致(transaction commit)。

## 後端要做的事(最小變動)

### 1. parse 函式從「吃檔案路徑」改成「吃 io.Reader」(機械式重構)

目前 `openCSV(path)` → `os.Open(path)`;改成從記憶體解壓的 zip 串流:

```go
func LoadFeedFromZip(blob []byte, prefix string) (*Feed, error) {
    zr, _ := zip.NewReader(bytes.NewReader(blob), int64(len(blob)))
    files := map[string]*zip.File{}
    for _, f := range zr.File { files[path.Base(f.Name)] = f }

    f := &Feed{...}
    rc, _ := files["stops.txt"].Open()
    f.parseStops(csv.NewReader(rc))   // 本來吃 path,現吃 reader

    rc, _ = files["routes.txt"].Open()
    f.parseRoutes(csv.NewReader(rc))

    // ...trips / stop_times / shapes / calendar / calendar_dates / frequencies 同理
    return f, nil
}
```

變動範圍:8 個 parse 函式的參數從 `path string` → reader。**RAPTOR / 等時圈 / API handler 零行。**

### 2. 背景自動 reload(零停機)

```go
var current atomic.Pointer[transit.Service]

func InitService(db *sql.DB) {
    svc := buildFromDB(db)
    current.Store(svc)
    go watchAndReload(db)
}

func watchAndReload(db *sql.DB) {
    var loaded time.Time
    // 開機立刻存時間,之後每小時檢查
    db.QueryRow("SELECT max(updated_at) FROM gtfs_bundle").Scan(&loaded)
    for range time.Tick(1 * time.Hour) {
        var newest time.Time
        db.QueryRow("SELECT max(updated_at) FROM gtfs_bundle").Scan(&newest)
        if newest.After(loaded) {
            svc := buildFromDB(db)   // 背景重建,同時舊的還在服務
            current.Store(svc)       // 瞬間切換,GC 收掉舊的
            loaded = newest
        }
    }
}

func buildFromDB(db *sql.DB) *transit.Service {
    feeds := make([]*gtfs.Feed, 0, 4)
    for _, name := range []string{"bus", "rail", "train"} {
        var blob []byte
        db.QueryRow("SELECT archive FROM gtfs_bundle WHERE feed=$1", name).Scan(&blob)
        f, _ := gtfs.LoadFeedFromZip(blob, name+":")
        feeds = append(feeds, f)
    }
    feeds = append(feeds, gtfs.SplitJumpfrog(feeds[0]))   // bus → jumpfrog
    rd, _ := raptor.Build(feeds)
    return &transit.Service{...}
}

// handler:
//   svc := current.Load()
//   svc.GetIsochrone(...)
```

### 3. 查詢時讀 current pointer

```go
func (s *Service) GetIsochrone(...) ... {
    svc := current.Load()
    return svc.query(...)
}
```

## 你不需要做的

- ❌ 不需要 rollout / 重啟
- ❌ 不需要改 RAPTOR
- ❌ 不需要改等時圈算法
- ❌ 不需要改 API endpoint
- ❌ 不需要 docker / helm / k8s 變動
- ❌ 不需要 cronjob

## DB 連線

用你現有的 dashboard-stream 連線,不加新的。這張表是 public schema。

## 什麼時候換資料

- DAG 每月(5、26 日)自動更新 `gtfs_bundle` → `updated_at` 變成新時間
- 後端每小時 poll → 發現 `newest > loaded` → 背景重建 → 原子切換
- 使用者完全無感,零停機
