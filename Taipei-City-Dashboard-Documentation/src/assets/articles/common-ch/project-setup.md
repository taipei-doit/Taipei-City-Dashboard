## 在本地運行專案

**_looks_one_** Fork [專案程式庫](https://github.com/taipei-doit/Taipei-City-Dashboard)，然後將專案 clone 到您的電腦。用 VSCode 或您偏好的程式編輯器開啟程式庫。

**_looks_two_** 透過開啟 Docker Desktop 或使用終端啟動 Docker 引擎。然後，開啟程式庫終端並移動至 `/docker` 資料夾 (`cd docker`)。

**_looks_3_** 在 docker 資料夾中，有一個 `.env.template` 檔案。複製該檔案並將其重新命名為 `.env`。大部分的變數已預填完成，而有些標記為 `[External Dev Don't Need to Fill]`。請不要更改上述變數的值。然而，您需要自行填寫以下 9 個變數：

```bash
## Docker image tag
...

## Frontend ENV Configs
...
VITE_MAPBOXTOKEN= # 參見資訊 1
VITE_MAPBOXTILE=mapbox:// # 參見資訊 2
VITE_PERSONAL_BOARD_UPDATE= # 參見資訊 3，此變數可依需求來做配置
...

## Server ENV Configs
...
DASHBOARD_DEFAULT_USERNAME= # 建立一個預設的管理員帳戶。填入任何使用者名稱。
DASHBOARD_DEFAULT_Email= # 建立一個預設的管理員帳戶。填入任何電子郵件。
DASHBOARD_DEFAULT_PASSWORD= # 管理員帳戶密碼。

## DB Configs
# Dashboard data DB
...
DB_DASHBOARD_PASSWORD= # dashboard 資料庫密碼。
...

# Dashboard Manager DB
...
DB_MANAGER_PASSWORD= # dashboardmanager 資料庫密碼。
...

# Redis Configs
...

# Qdrant Configs
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY= # Qdrant 密碼（必填）。此處必須填入 Qdrant 的存取密碼，否則無法連線。
QDRANT_COLLECTION_NAME=query_charts

# pgadmin
PGADMIN_DEFAULT_EMAIL= # 建立一個預設的 pgadmin 帳戶。填入任何電子郵件。
PGADMIN_DEFAULT_PASSWORD= # pgadmin 帳戶密碼。
...
```

> **i01**
> 用 Mapbox 金鑰填寫變數 `VITE_MAPBOXTOKEN`，這將允許此專案中的地圖被渲染。透過建立一個 Mapbox 帳戶並按照[此指南](https://docs.mapbox.com/help/getting-started/access-tokens/)建立您自己的 Mapbox 金鑰。如果您不使用 Mapbox 帳戶的預設公開金鑰，請記得將 https://localhost:8080 添加到您的金鑰支援的 url 列表中。

> **i02**
> 此變數會在地圖上添加一個 3D 建物圖層。此步驟為可選，可以將變數留空。
>
> 首先，[在此處](https://1drv.ms/u/c/0d57c13a41c62975/Ediuy_ijtO5InxtXHs5SNo0B68bioV7CkqQQRRyuLivSXA?e=mdgoda)下載模型檔案(`geojson`)。然後，打開 Mapbox Studio 並移動到["Tilesets"](https://studio.mapbox.com/tilesets/)。點擊"New Tileset"並上傳下載的文件。上傳完成後，打開 tileset 並點擊"share & use"。複製"Tileset ID"並將其添加到`.env`文件中的變數`VITE_MAPBOXTILE`（貼在"mapbox://"後面）。
>
> 返回 MapBox 上的 tileset。在螢幕的左側，您會看到一個名為"Vector Layers"的側欄。複製標題下方的圖層名稱（應以"tp_building_height"開頭）。然後，返回到程式庫並移動到`/src/assets/configs/mapbox/mapConfig.js`。找到一個名為"TaipeiBuilding"的物件，並將"source-layer"參數替換為您複製的圖層名稱。

> **i03**
> 此變數為3.0新增，用於控制個人儀表板的自動更新頻率。可以將此變數留空，之後根據需要配置您的個人儀表板更新頻率。
>
> 參數格式定義：個人儀表板index:更新頻率(秒),個人儀表板index:更新頻率(秒)，使用逗號區隔多個儀表板設定。
> 
> 配置範例：
> 
> `VITE_PERSONAL_BOARD_UPDATE`=71528009ae4b:600,415dc056e6df:600,278b42f7d039:600,f7a3542955f1:600
>
> 上述範例表示四個不同的儀表板（由index識別），每個儀表板均設定為600秒（10分鐘）自動刷新一次。
> 

**_looks_4_** 在終端中，依次執行以下指令以建立一個 docker network 並啟動容器。

> **t01**
> 如果您遇到任何問題，請檢查 docker logs。常見的錯誤包括`.env`文件填寫不正確，Docker 引擎未啟動，網絡設定不正確，或者在執行指令之前未刪除 volumes(如果存在), 請執行`docker compose -f docker-compose-db.yaml down -v`, 


建立一個名為`br_dashboard`的 Docker network。

```bash
docker network create --driver=bridge --subnet=192.168.128.0/24 --gateway=192.168.128.1  br_dashboard
```

啟動與 DB 及 Qdrant 相關的容器。執行此指令後，檢查所有容器是否正在運行。在執行下一個指令之前，請等待資料庫完全初始化（檢查 docker logs 並檢查輸出中是否有 `database system is ready to accept connections`）。注意：本地環境必須啟用 Qdrant 容器才能正常使用 Chatbot 功能。

```bash
docker-compose -f docker-compose-db.yaml up -d
```

初始化前端和後端環境。此指令建立的容器是暫時性的。請等待容器停止運行後再運行下一個指令。

```bash
docker-compose -f docker-compose-init.yaml up -d
```

> **i04**
> 在 docker-compose-init.yaml 文件中，有三個容器被賦予以下任務：
>
> `dashboard-fe-init`：執行 npm install；`dashboard-be-init-manager`：初始化 dashboardmanager DB；`dashboard-be-init-dashboard`：初始化 dashboard DB。

啟動前端和後端服務：

> **w01**
> 下方指令也會啟動一個 Nginx 服務. 如果您不需要 `https`，請將 `/docker/nginx/conf.d/default.conf` 中 11-15 行註解掉 ; 如需要，請產生一個 ssl 憑證 (`citydashboard-fullchain1.pem`) 與 private key (`citydashboard-privkey.pem`) 並儲存於 `/docker/nginx/ssl`。

```bash
docker-compose up -d
```

> **t02**
> 前端支持熱重載，所以您可以對程式碼進行修改並在瀏覽器中直接看到變化(如為 Windows 用戶，請於 `vite.config.js` 中的 `server` 屬性裡加入 `watch: {usePolling: true}`)。
>
> 後端不支持熱重載。如果您對後端程式碼進行了修改，您將需要重啟`dashboard-be`容器。

> **i05**
> 從現在開始，如果您想重新初始化資料庫，請按照以下步驟操作：
>
> 首先，確保所有相關的容器都已關閉或刪除。接著，刪除volumes `docker compose -f docker-compose-db.yaml down -v`。最後，執行上述三個 `docker-compose` 指令。

**_looks_5_** 專案現在應該已在本地運行。打開您的瀏覽器並開啟 [https://localhost:8080](https://localhost:8080)。您應該會看到儀表板首頁。如要用帳密登入，請打開登入視窗，按住`shift`鍵並點擊 DOIT Logo。如果您遇到任何問題，請檢查 docker logs 或瀏覽器中的 console。

## 進一步的開發設定

### PGAdmin

請按照以下步驟操作以在 pgAdmin 中匯入兩個 Postgres 資料庫：

**_looks_one_** 打開 pgAdmin (https://localhost:8889/login) 並使用您在 `.env` 文件中填寫的帳號密碼登入。然後，在左上角的 "Servers" 按紐按右鍵並選擇 "Register" > "Server..."。在 "General" 分頁中，將 "Name" 填入 `dashboard`。然後，在 "Connection" 標籤中，將 "Host name/address" 填入 `postgres-data`，"Username" 填入 `postgres`，並將 "Password" 填入您在 `.env` 文件中填寫的密碼 (`DB_DASHBOARD_PASSWORD`)。點擊 "Save" 然後 "Connect"。

**_looks_two_** 重複第一步，但在 "General" 標籤中，將 "Name" 填入 `dashboardmanager`。並在 "Connection" 標籤中，將 "Host name/address" 填入 `postgres-manager`，並將 "Password" 填入您在 `.env` 文件中填寫的密碼 (`DB_MANAGER_PASSWORD`)。點擊 "Save" 然後 "Connect"。

### Postman

為了測試本專案的 API，我們建議使用 Postman。API 的 collection 可以在<a href="/documentation/data/dashboard_postman.json" download>這裡</a>下載。下載檔案後，打開 Postman 並點擊 "Import" > "Choose Files"，然後選擇下載的檔案。Collection 將會被添加到您的 Postman 工作區。同時也請匯入<a href="/documentation/data/dashboard_postman_env.json" download>這個</a>環境設定檔 ，並在 Postman 介面的右上角選擇環境。

### Qdrant 向量資料庫與資料匯入

此步驟用於將 PostgreSQL 資料庫中的資料轉換為向量嵌入，並上傳至 Qdrant 向量資料庫以供搜尋使用。

**_looks_one_** 確保 Qdrant 服務已啟動。在您執行 `docker-compose -f docker-compose-db.yaml up -d` 時，Qdrant 服務 (`qdrant`) 應已一同啟動。

**_looks_two_** 執行資料匯入工具。此工具會將 PostgreSQL 中的資料轉換為向量並寫入 Qdrant。在 `docker` 目錄下執行：

```bash
docker compose --profile tools up vector-db-upgrade
```

> **i06**
> 首次執行時會自動下載 AI 模型 (約 500MB)，請耐心等待。若需查看詳細執行紀錄，可移除 `-d` 參數。若遇到記憶體不足錯誤，請參考 `docker/qdrant-upgrade/README.md` 進行調整。