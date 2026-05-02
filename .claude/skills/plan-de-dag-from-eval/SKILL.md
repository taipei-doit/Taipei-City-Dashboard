---
name: plan-de-dag-from-eval
description: 從題目評估報告（智慧通勤、智慧治理等領域題目的 .md 文件）產出 Taipei-City-Dashboard-DE 的「DE 實作規劃」文件，內容含資料源確認、實際欄位對照、排程建議、骨架對照 DAG、PostgreSQL schema、**BE API contract（endpoint × response type × SQL）**、實作順序、關鍵決策等 §1～§11 結構。**主動使用情境**：使用者說「為 XXX 評估報告寫 DE 規劃」「把這份評估報告轉 DE 實作」「設計這個儀表板的 ETL」「規劃 XXX 儀表板的資料工程」「DE planning for ...」「依這份題目寫一份規劃」「依 XX_儀表板二 寫」等等。**不要使用**：使用者要的是 DAG 程式碼實作（不需要規劃，要寫 code）、要修改既有規劃、或評估報告本身的內容。
---

# 從題目評估報告產出 DE 實作規劃文件

把評估報告轉成可執行的 DE 設計文件。每份規劃覆蓋一個儀表板，遵循 §1～§11 結構，並**強制抓真實樣本**避免「依頁面描述合理推測」導致 schema drift。

## 為什麼要強制抓樣本

過去看到的失敗模式：評估報告說「異常公告含開始/結束時間、設施類別」，但 data.taipei 實機抓的 dataset 只有「日期時間（單一）」與「說明」全文，欄位 4/5 都不存在。沒抓樣本就寫 schema，每一支 DAG 都會在第一次跑時 KeyError。

樣本資料源類型不一定是 `data.taipei` — 可能是 TDX、新北市開放、政府開放、TDD、私有 API、CSV、KML、Shapefile。skill 內依來源類型用對的抓法（見 Step 3）。

## 工作流（必照順序）

### Step 0. 接收輸入

從 user 對話取得：
- **評估報告檔案路徑**（必填，.md 文件）
- **儀表板編號**（一/二/三/...）— 一份報告通常含 N 個儀表板，一次只規劃一個

如果 user 沒明確說，主動問。如果評估報告檔很長（>500 行），讀「目錄」與該儀表板對應的章節就好。

### Step 1. 讀評估報告

用 Read tool 讀完整報告，extract：

- 該儀表板的需求描述（components C1～CN）
- 資料源（dataset 名稱、識別碼如 `00001517`、page_id、URL、API endpoint）
- 排程建議（如「DAG 共用 `*/5 * * * *`」— 評估常給太頻繁的建議，要重新評估）
- 預期 charts / 表格 / 地圖視圖

**特別注意**：評估報告寫的「設施類別 / 開始時間」等欄位，幾乎都是「依頁面描述合理推測」，**不可信**，必經 Step 3 樣本驗證。

### Step 2. 在 codebase 找對照 DAG

掃 `Taipei-City-Dashboard-DE/dags/proj_city_dashboard/*/job_config.json`，依下列條件篩出最像的 1～2 支 DAG 當「結構骨架對照」：

| 條件 | 比對欄位 |
|---|---|
| `load_behavior` 一致 | `dag_infos.load_behavior` |
| 資料源類型一致 | `data_infos.source_type`（如 `data.taipei api` / `data.taipei csv file` / `tdx api` / `government open data`） |
| 是否含 geometry 一致 | `data_infos.is_geometry` |
| schedule 級距相近 | `dag_infos.schedule_interval`（每月 vs 每日 vs 高頻） |

優先順序：`page_id pattern + 純 DataFrame + current+history` 是最完整對照（cf. [`env_srv_energy_subsidy/`](Taipei-City-Dashboard-DE/dags/proj_city_dashboard/env_srv_energy_subsidy/)）。`page_id + Point geometry + replace` 對照 [`D020105/`](Taipei-City-Dashboard-DE/dags/proj_city_dashboard/D020105/)。

### Step 3. 抓真實資料樣本（**必做**，不可省略）

依資料源類型用對應方式抓 1–3 筆樣本：

#### data.taipei page_id（最常見）

```bash
PAGE_ID="<UUID>"
# 1. 取當前 rid
curl -s "https://data.taipei/api/frontstage/tpeod/dataset.view?id=$PAGE_ID" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); rs=d['payload']['resources']; [print(r['rid'], '|', r['name'], '|', r['format']) for r in rs]"
# 2. 取樣本（用第 1 步的 rid）
curl -s "https://data.taipei/api/v1/dataset/<RID>?scope=resourceAquire&limit=3" | python3 -m json.tool
# 3. 若有 geometry，多看幾筆判斷 CRS（座標範圍）
curl -s "https://data.taipei/api/v1/dataset/<RID>?scope=resourceAquire&offset=0&limit=1000" | python3 -c "..."
```

#### TDX（運輸資料平臺）

```bash
# 需要 client_id / secret，問 user 提供。skill 不會自己有 token
TDX_CLIENT_ID="..."  # 由 user 提供
TDX_CLIENT_SECRET="..."
TOKEN=$(curl -s -X POST "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token" \
  -d "grant_type=client_credentials&client_id=$TDX_CLIENT_ID&client_secret=$TDX_CLIENT_SECRET" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -H "Authorization: Bearer $TOKEN" "<TDX endpoint>?\$top=3&\$format=JSON" | python3 -m json.tool
```

#### 新北市開放資料 / 一般 JSON API

```bash
curl -s "<URL>" | python3 -m json.tool | head -50
# 或單筆
curl -s "<URL>" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d[0] if isinstance(d, list) else d, ensure_ascii=False, indent=2))"
```

#### CSV

```bash
curl -s "<URL>" | head -5  # 先看 header + 2 筆
curl -s "<URL>" | wc -l    # 看總筆數
```

#### GeoJSON / Shapefile

```bash
# GeoJSON
curl -s "<URL>" | python3 -c "import sys,json; d=json.load(sys.stdin); f=d['features'][0]; print('properties:', f['properties']); print('geom_type:', f['geometry']['type']); print('coord sample:', f['geometry']['coordinates'][:2] if isinstance(f['geometry']['coordinates'][0], list) else f['geometry']['coordinates'])"

# Shapefile（已有 utils/extract_stage.py:467 get_shp_files_merge）
# 抓樣本：下載 zip → unzip → 用 geopandas 讀 .shp 看 schema
```

#### 樣本必記錄項

- 完整欄位中文鍵 list（每個欄位的中文名）
- 至少 1 筆樣本值
- 總筆數（count / 全數抓出後 len）
- 若有時間欄：時間格式（如 `20260420T213100` 是 ISO8601 無分隔）
- 若有 geometry：座標範圍判斷 CRS（121.x, 24.9x = WGS84；20xxxx, 27xxxx = TWD97/EPSG:3826）
- 若有 `_importdate`：記錄它的格式

### Step 4. 與評估報告假設交叉比對

針對評估報告中提到的每個「預期欄位」，逐一對照樣本是否存在：

```
規劃推測欄位       樣本實況         結論
車站              ✓ 存在            直接 rename
設施類別          ✗ 不存在          要從說明文字 parse 或刪掉這個 chart
異常起始時間       ✗ 不存在          只有「日期時間」單一欄
```

差異要列為**修正紀錄**，寫進規劃文件 §11。**不要默默套用評估報告的欄位假設**。

### Step 4b. 欄位缺失時的處理順序（**禁止直接改主題**）

發現評估報告假設的欄位在資料集中不存在時，**必須照這個順序處理，不能跳步**：

#### 4b-1：先查同題目其他 dataset 有沒有可 JOIN 的欄位

- 列出同一份評估報告中提到的所有其他資料集
- 確認有沒有含缺失欄位、且可以用 station / ID / 地點等 key JOIN 回來的資料集
- **範例**：`00001517`（捷運異常）沒有 `equipment_type`，但 `00001516`（電梯座標）有 `facility_type`，可以 `JOIN ON station_name` 還原設施類型
- 找到可 JOIN 的路徑 → **用 JOIN 解決，不改主題**，在 §11 記錄「欄位來源修正：從 XX 資料集 JOIN 取得」

#### 4b-2：確認無法 JOIN 後，才允許改主題——但要明確標記

若確認所有資料集都無法補齊欄位，才進入主題替換。此時 §11 修正紀錄**必須**包含：

```
⚠️ 此修正改變 component 主題

- Component：C3
- 評估報告原意（引用行號）：[評估報告 L303]
  > 異常類型圓餅圖（電梯／坡道／其他），GROUP BY equipment_type
- 缺失欄位：equipment_type（在 00001517 查無此欄）
- 已查 JOIN 可能性：
  - 00001516（電梯座標）：facility_type 存在 ✓ → **此路徑可行，不應到此步**
  - （若真的全查無）標明「查了 N 個資料集，均無可 JOIN 欄位」
- 替代主題：<改成什麼>
- 替代理由：<為何這個替代主題仍在合理範圍>
- 需通知：BE / FE 開發者、使用者確認
```

**主題改變前須暫停，告知使用者並等確認**，不能自行決定。

### Step 5. 寫規劃文件

照下列 §1～§11 結構，全部章節都寫（不省略）。每節該寫什麼見 [references/doc-structure.md](references/doc-structure.md)。

```
# <儀表板標題>｜<重點 keyword> — DE 實作規劃

> 規劃日期：<today>
> 對應評估報告：[<原檔名>](<原檔名>)
> 範圍：聚焦 Taipei-City-Dashboard-DE 端（Airflow DAG + PostgreSQL 落庫），並含交給 BE 的 **API contract（endpoint × response type × SQL）** 作為下游接力依據。FE 渲染細節不在本文件規劃範圍。

## 1. 資料源確認（page_id 與 rid 已查到 / API endpoint 已確認）
## 1.1 實際欄位（已抓樣本驗證 <today>）
## 2. 對「DAG 共用」的修正建議（若評估原文有提）
## 3. 既有可用工具盤點（不需重造輪子）
## 3.1 骨架對照 DAG（已實證）
## 4. 目錄與檔案結構
## 5. DAG A：<dag_id> — <主題>
## 6. DAG B：<dag_id> — <主題>（若該儀表板需要 2 支 DAG）
## 7. 已知風險與緩解
## 8. 對 BE 的接口（API contract + chart query）
## 8.1 API Contract（endpoint × method × response type × FE 渲染）
## 8.2 各 endpoint 對應的 SQL
## 8.3 Response 欄位語意說明
## 9. 實作順序（建議 1 個工作日完成）
## 10. 關鍵決策請確認後再動工
## 11. 修正紀錄（<today> 抓樣本後）
```

#### 重要寫作原則

- **§1.1 一定要寫**：列實際欄位 vs 規劃用名，標註「來源無此欄」「需從 X parse」
- **§3.1 一定要列具體 DAG**：不要說「參照 accessible_facilities/」這種模糊指引；要明確指出「mrt_a11y_alert 對照 [env_srv_energy_subsidy/]，理由：page_id + 純 DataFrame + current+history」
- **§5 / §6 程式碼骨架**：rename mapping、status 邏輯、station 命名統一都要符合樣本實況。**禁止寫評估報告假設的欄位**
- **§7 風險表至少 5 項**：data.taipei API 偶空、欄位中文鍵不確定、來源更新頻率不明、station 命名一致性、history 表累積、開發遺留 print
- **§8 BE 接口分三段都要寫**：
  - **§8.1 API Contract 表**：每個 component 一行，欄位含 `Endpoint`、`Method`（一律 GET）、`Response type`（`two_d` / `three_d` / `percent` / `map_legend` 四選一，對齊 `Taipei-City-Dashboard-BE/app/models/componentData.go` 的 `TwoDimensionalDataOutput` / `ThreeDimensionalDataOutput` / `MapLegendData`）、`FE 渲染元件`。Endpoint 命名走 `/api/v1/<domain>/<subdomain>/<metric>` pattern（如 `/api/v1/mrt/a11y/alert-count`）。**禁止自訂新型別**，除非樣本資料形狀真的塞不進四種標準。
  - **§8.2 各 endpoint SQL**：每個 endpoint 一條，用樣本驗過的欄位（禁用評估報告假設欄位）。如有特殊處理（`LATERAL JOIN`、`DISTINCT ON`），SQL 後加 blockquote 說明為何。
  - **§8.3 Response 欄位語意**：每個 endpoint 列出 response 內每個欄位的意思、允許值、單位（如 `x` 是日期字串 `YYYY-MM-DD`、`y` 是該日異常筆數整數、`type` 允許 `active`/`closed`），讓 BE/FE 不需回頭翻 DE plan 也能對齊。
- **§10 至少 2 個決策**：通常包含「是否拆 DAG」、「是否 current+history」、「status / 分類規則」

### Step 6. 自動命名 + 寫檔

輸出與評估報告同目錄。命名 pattern：

```bash
# 嘗試從同目錄推命名規則
EVAL_DIR="$(dirname <評估報告路徑>)"
EVAL_STEM="$(basename <評估報告路徑> .md)"

# Rule 1: 若同目錄已有 _DE實作規劃_ 檔，沿用其前綴
EXISTING="$(ls "$EVAL_DIR"/*_DE實作規劃_*.md 2>/dev/null | head -1)"
if [ -n "$EXISTING" ]; then
  PREFIX="$(basename "$EXISTING" | sed 's/_DE實作規劃_.*//')"
  OUTPUT="$EVAL_DIR/${PREFIX}_DE實作規劃_儀表板${中文編號}.md"
else
  # Rule 2: 用評估報告 stem 直接後綴
  OUTPUT="$EVAL_DIR/${EVAL_STEM}_DE實作規劃_儀表板${中文編號}.md"
fi
```

「中文編號」對照：1→一、2→二、3→三、4→四、5→五。

寫檔用 Write tool。

### Step 7. 回報

對 user 印簡短 summary：

```
✅ DE 規劃已產出
   檔案：<OUTPUT>
   行數：~XXX 行

關鍵發現：
   - 資料源 <名稱>：<count> 筆，欄位 N 個
   - <若有重大 schema 偏差>：原規劃假設 X 欄位，實際只有 Y → 已記入 §11
   - 對照骨架：<dag_folder/>

§10 待 user 拍板的決策：
   1. <決策 1>（推薦：A）
   2. <決策 2>（推薦：B）

確認後可執行 §9 實作步驟。
```

### §11 修正紀錄格式規範

每一處偏離評估報告的修正，都要填一行進修正紀錄表：

| # | Component | 修正類型 | 評估報告原意（行號） | 修正後內容 | 主題改變 | 原因 |
|---|---|---|---|---|---|---|
| 1 | C2 | 欄位 alias | `line`（L302） | `line_name AS line` | ❌ 否 | 欄位名不同，alias 對齊 |
| 2 | C3 | JOIN 補欄位 | `equipment_type`（L303） | JOIN 00001516 取 `facility_type` | ❌ 否 | 欄位在另一資料集，JOIN 還原 |
| 3 | C3 | **主題改變** | 異常類型圓餅（L303） | 30 天趨勢折線 | ⚠️ **是** | 欄位不存在且無可 JOIN 來源 |

**「主題改變」欄標 ⚠️ 是 的行**，必須額外附上 4b-2 的完整說明區塊。沒有說明區塊的主題改變視為**未登記的偷改**，`integration-audit` 會把它標為偏離。

## 處理常見錯誤

| 錯誤 / 阻塞 | 處理 |
|---|---|
| 評估報告找不到該儀表板章節 | 列出評估報告中找到的所有儀表板編號給 user 選 |
| data.taipei API 503 / 空 list | 重試 3 次；若仍失敗，改抓 CSV fallback（見 utils `download_file`） |
| TDX 沒 token | 停下問 user 索取 client_id / secret，或請他先抓樣本 paste 給你 |
| 來源欄位中文鍵很怪（如 `tmpx`/`tmpy`/`gtag_longitude`） | 仍照寫 mapping，但在 §1.1 註明「欄位命名不直觀，建議聯絡資料 owner」 |
| 樣本回 0 筆 | 不能跳過，**必須**處理 — 通常代表來源 API 變動，要在 §7 列為高風險 |

## 為什麼這樣設計

- **強制抓樣本（Step 3）**：上次 mrt_a11y_alert 規劃時沒抓樣本，4/5 預期欄位都對不上、整個 schema 重做。這個痛點不能重演
- **§11 修正紀錄**：透明標記「原假設 vs 實況」差異，未來 review 知道為何這樣決定
- **依來源類型分流抓法**：data.taipei 與 TDX 與 CSV 的 query 方式完全不同，預設一律走 data.taipei 會 silent fail
- **不一次產 N 份規劃**：一次一個儀表板讓 user 能逐一審閱、調整 §10 決策；批量產出反而難 review
- **依評估報告同目錄沿用命名**：保持文件樹整齊，user 不需指定輸出路徑
- **不自動修評估報告**：評估報告是上游文件，DE 規劃只是下游推演 — 若評估有錯，回頭改評估而不是讓規劃 silent fix

## 互動風格

- 開始前一句「即將為 <評估報告 stem> 儀表板 X 產出 DE 規劃，預計 5–10 分鐘…」
- Step 3 抓樣本前一句「正在抓 <資料源名稱> 樣本驗證欄位…」
- Step 5 寫檔前一句「樣本確認完成，發現 N 處與評估報告不符，正在寫 §11 修正紀錄…」
- 最後 summary 用 Step 7 格式
