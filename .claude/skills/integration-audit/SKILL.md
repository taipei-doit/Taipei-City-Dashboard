---
name: integration-audit
description: 對 Taipei City Dashboard monorepo（DE + BE + FE + DB）做跨層整合健檢，找出 FE↔BE↔DB↔DAG 之間的命名 / shape 不對齊、孤兒 endpoint / 孤兒 DB 表、FE 殘留 mock 與寫死陣列、服務 port 衝突、規劃但未實作的功能等問題，產出結構化 markdown 報告到 `./.claude_output/INTEGRATION_ISSUES.md`。**主動使用情境**：使用者說「整合問題盤點」「整理一下整合問題」「FE BE 對齊嗎」「BE 跟 DB 對齊」「DE DAG 跟 BE 對齊嗎」「整合健檢」「mock 還剩哪些」「孤兒 endpoint」「孤兒表」「monorepo 健檢」「為什麼 dashboard 沒資料」「merge 完想做整合檢查」等等，**剛 merge 進新功能 / 新 DAG / 新 view 之後也應主動建議使用**。**不要使用**：使用者只想看單一檔案、改某個 bug、單層 code review、純探索而非比對。

---

# Taipei City Dashboard 跨層整合健檢

對整個 monorepo 做雙向比對，找出各層之間沒對齊的地方。**這個 skill 的核心不是「找東西」而是「比對」**：FE 期望的 API 跟 BE 實作對得上嗎？BE query 用的表 FE 真的有用到嗎？DAG 抓的欄位跟 BE 用的對得上嗎？

## 何時使用

- 一輪 merge 之後想做 health check
- demo 前確認所有 component 都接通了
- 看到某個圖空白 / 顯示「組件資料異常」想排查根因
- 想知道哪些 BE endpoint 是孤兒（無人呼叫）、哪些 DB 表沒上儀表板
- 接手新人想快速理解整套服務的耦合狀態

## 產出規則

**唯一輸出**：`./.claude_output/INTEGRATION_ISSUES.md`（從 repo root 算的相對路徑）。
- 每次跑都覆蓋，不留歷史（要看歷史看 git log）
- 在 chat 也給一份短版摘要（前三大問題 + 報告連結）
- 開工前先 `mkdir -p ./.claude_output` 確保資料夾存在

## 工作流程

依序做這 6 大類檢查。每類都用「**雙向比對**」的思考 — 不要單方面列舉，要列出兩邊各自有什麼然後比對 mismatch。

### 1. FE ↔ BE endpoint 對齊

**找 FE 期待打哪些 path**：
```bash
grep -rnE 'axios\.(get|post|put|delete|patch)\(' Taipei-City-Dashboard-FE/src/ \
  | grep -v node_modules
grep -rnE '"/api/v[0-9]+/' Taipei-City-Dashboard-FE/src/ | grep -v node_modules
```

**找 BE 註冊了哪些 route**：
```bash
grep -nE 'RouterGroup|\.Group\("/|\.GET\(|\.POST\(|\.PUT\(|\.DELETE\(' \
  Taipei-City-Dashboard-BE/app/routes/router.go
```

**找 FE mock middleware 攔截哪些 path**（這些是 BE 沒做才被 mock）：
```bash
cat Taipei-City-Dashboard-FE/mock/index.js  # 看 routes map
```

**比對輸出 table**：

| FE 期待 path | BE 實作 path | DB 表 | 狀態 |
|---|---|---|---|
| /xxx | (無) | — | FE mock，BE 沒對應 |
| (無) | /yyy | zzz | BE 孤兒 |

**判斷**：path 大致 1:1 但拼字 / 命名不同（例：`station-overview` vs `stations`）通常是雙方各做各的、沒同步 contract，要列為嚴重。

### 2. BE ↔ DB 表使用情況（孤兒表偵測）

**列出 DB 所有業務表**：
```bash
docker exec postgres-data psql -U postgres -d dashboard -c '\dt' 2>&1
docker exec postgres-manager psql -U postgres -d dashboardmanager -c '\dt' 2>&1
```

**找 BE 哪些 query 引用哪張表**：
```bash
grep -rnE 'FROM [a-z_]+|UPDATE [a-z_]+|INSERT INTO [a-z_]+|JOIN [a-z_]+' \
  Taipei-City-Dashboard-BE/app/models/ | grep -v _test.go
```

**找 BE table struct 定義**：
```bash
grep -rnE 'TableName\(\) string|gorm:"column' Taipei-City-Dashboard-BE/app/models/ \
  | grep -v _test.go | head -50
```

**比對**：
- DB 有表但 BE 完全沒 query → **孤兒表**
- BE 有 query 但 FE 沒呼叫對應 endpoint → **孤兒 endpoint**（接 DB 但無人用）

對每張表查實際行數判斷有沒有資料：
```bash
docker exec postgres-data psql -U postgres -d dashboard -c \
  'SELECT COUNT(*) FROM <table>;'
```

### 3. FE 殘留 mock / 寫死陣列

**全文搜 mock 痕跡**：
```bash
grep -rnE 'mock|MOCK|dummy|fake|hardcoded|TODO|FIXME|寫死|假資料' \
  Taipei-City-Dashboard-FE/src/ Taipei-City-Dashboard-FE/mock/ \
  2>/dev/null | grep -v node_modules
```

**搜 view 內 inline 大陣列**（chart 資料但沒走 API）：
```bash
grep -rnE 'const \w+ = \[|: \[$' Taipei-City-Dashboard-FE/src/views/ \
  | grep -v node_modules
```

**檢查項目**：
- `mock/index.js` 中還剩哪幾條 mapping？對應 BE 是否已實作？
- `mock/*.json` 有哪些是 dead file（mapping 已移除但 JSON 還在）
- `*.vue` 內 inline `slopeCounts` / `workCounts` / GeoJSON 等寫死資料 — 對應 BE 跟 DAG 是否存在

### 4. DE DAG ↔ DB 表 ↔ BE 對齊

**列出所有 DAG**：
```bash
ls Taipei-City-Dashboard-DE/dags/proj_city_dashboard/
```

**對每支 DAG 的目標表**：
```bash
grep -rnE 'TABLE_NAME|target_table|table_name' \
  Taipei-City-Dashboard-DE/dags/proj_city_dashboard/<dag>/
```

**比對**：
- DAG 寫進的表 → BE 有 query 用嗎？
- BE 期待的欄位 → DAG 真的有抓進來嗎？（看 column 不齊）
- DAG 的 schedule 跑了嗎？最近一次 dag_run 是何時？

```bash
docker exec develop-airflow-scheduler-1 airflow dags list-runs -d <dag_id> 2>&1 | head
```

### 5. 服務狀態與 port 衝突

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker ps -a --format 'table {{.Names}}\t{{.Status}}' | grep -vE 'Up|Exited \(0\)'
```

**檢查項目**：
- 哪些容器 `Created` / `Exited (1)` / `Restarting` — 都是異常
- docker-compose 定義了但沒跑的服務：
  ```bash
  cd docker && docker compose config --services 2>&1
  ```
  跟 `docker ps` 比對
- HTTP smoke：`curl -sk -o /dev/null -w '%{http_code}\n' <url>` 對 FE / BE / Nginx / Airflow / pgAdmin

### 6. 規劃但未實作

**找註解 / TODO 寫但 code 沒做的**：
```bash
grep -rnE 'TODO|FIXME|XXX|將以|將會|預計|尚未實作|not yet implemented' \
  Taipei-City-Dashboard-FE/src/ Taipei-City-Dashboard-BE/app/ \
  Taipei-City-Dashboard-DE/dags/ 2>/dev/null | grep -v node_modules | head -30
```

特別注意 `BE 將以 ... 回傳`、`每 X 分鐘輪詢` 等已寫進 source comment 但實際沒做的 — 是強訊號：規劃在前、實作沒跟上。

## 報告模板

寫到 `./.claude_output/INTEGRATION_ISSUES.md`，**嚴格**用這個結構（讓不同次的 audit 報告好做 diff）：

```markdown
# Taipei City Dashboard 整合問題清單

產出日期：YYYY-MM-DD
產出範圍：FE + BE + DE + DB
分支：<current-branch>（最近 merge：<最近 5 個 merge commit subject>）

---

## 🔴 嚴重：FE / BE 命名與 shape 不對齊

<table 對應 §1>

→ 一句結論建議哪邊改

## 🟡 DB 表沒人用（孤兒）

<table 對應 §2>

## 🟡 FE 殘留靜態資料

<table 對應 §3，含路徑 + 行號 + 內容>

## 🟡 DE DAG 與下游對齊

<table 對應 §4>

## 🟡 規劃但未實作

<bullet list 對應 §6，含 file:line + 註解原文>

## 🟢 服務狀態（pass through）

| 服務 | URL/Port | 狀態 |
|---|---|---|
| ... | ... | ✅/⚠️/❌ |

## 🟢 設計層面（次要 / 清債）

<bullet list — 例如 FE 沒 API service layer、SQL 重複可抽 helper>

---

## 建議優先順序

1. ...
2. ...
3. ...

## 對齊方案備選（給最大宗的 mismatch 模組）

### 選項 A：BE 補出 FE 期待
### 選項 B：FE 改打 BE 既有
### 選項 C：兩邊都動，統一命名
```

每個方案列出具體要改的檔案 + 預估工作量（分 / 時 / 天）。

## 寫報告的原則

1. **資訊密度高、不灌水**：用 table 不要用 bullet 群組，每行一個事實。
2. **附 file:line**：找到問題引用具體位置，方便 click 過去。
3. **誠實**：找不到問題的類別就寫「無發現」，不要硬湊。
4. **建議要 actionable**：「應對齊命名」太空泛；「將 FE `MrtAccessibilityView.vue:135` 的 `/station-overview` 改打 BE 既有 `/stations`，並重寫 C4 component 為 map marker」才實用。
5. **保留 emoji 分級**（🔴/🟡/🟢）讓人一眼看到優先級。
6. **不要把 session 中的 sidewalk 改動寫進去**：這份報告是當下整合狀況，不是「我做了什麼」的紀錄。

## 跑完之後給 chat 的摘要

報告寫完後，在 chat 輸出 ~10 行摘要：

```
INTEGRATION_ISSUES.md 已更新到 ./.claude_output/

🔴 嚴重 (N 項)：<最關鍵 1 項>
🟡 中度 (N 項)：<最關鍵 1 項>
🟢 已過 (N 項)

下一步建議：<從報告抽 1-2 句>
完整內容：[INTEGRATION_ISSUES.md](.claude_output/INTEGRATION_ISSUES.md)
```

不要把整份報告貼進 chat — 寫進檔案，chat 給導引就好。

## 工具與環境假設

- repo root：執行 skill 時應該已經在 `Taipei-City-Dashboard/` 下；如不在，先 `cd` 過去
- DB / Airflow / FE / BE 容器都跑著（`docker ps` 看得到）— 如果某些沒跑，在「服務狀態」section 標注，**不要**因此中止 audit；其他類別的檢查仍可照常
- 不需要 `npm install` / `go build` — 純 read-only 分析，靠 grep + docker exec 就夠
- 不要修改任何 source code — 這是 audit 不是 fix；改動要等使用者另外指示

## 大致時間預期

完整跑一次約 2-5 分鐘，視 monorepo 大小跟服務數量。並行用 Bash multi-command 可加速。
