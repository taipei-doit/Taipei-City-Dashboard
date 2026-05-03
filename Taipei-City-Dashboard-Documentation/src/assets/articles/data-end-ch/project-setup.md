本指南提供使用 Docker 構建和啟動 Airflow 環境的逐步過程。

## 先決條件

開始之前，請確保已安裝 Docker 與 Docker Compose。

> **w001**
> 若你使用 Docker Desktop，應將 Docker engine 的 RAM 分配至 6 GB 以上（理想為 8 GB 以上）。
> 可於 Docker Desktop 介面的右上角齒輪進入 Settings，在 `Settings/Resources/Memory limit` 調整並重新啟動 Docker。

### Step 1: 建立一個新的 Docker Image

首先，打開你的終端，確保你位於包含 Dockerfile 的 `local-env` 目錄中。使用以下指令建立名為 `myairflow`, tag 為 `2.7.3` 的 Docker Image：

```bash
docker build -t myairflow:2.7.3 .
```

### 第二步：創建 .env 文件

在當前目錄（docker-compose.yaml 所在目錄）中創建一個 `.env` 文件，並添加以下內容：

```bash
AIRFLOW_IMAGE_NAME=myairflow:2.7.3
AIRFLOW_UID=50000
AIRFLOW_PROJ_DIR=../
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow
```

**_looks_one_** `AIRFLOW_IMAGE_NAME`: 剛構建的 Docker Image 的名稱和 tag。

**_looks_two_** `AIRFLOW_UID`: Airflow 使用的用戶 ID。

**_looks_3_** `AIRFLOW_PROJ_DIR`: 你的 Airflow 專案目錄。

**_looks_4_** `_AIRFLOW_WWW_USER_USERNAME` 與 `_AIRFLOW_WWW_USER_PASSWORD`: Airflow 預設的網頁界面帳號和密碼。

這些環境變量將在 Docker Compose 中用於設定 Airflow 的基本配置。

### 第三步：啟動 Docker Compose

1. 建立 docker network：在啟動 docker-compose 之前，請先確保 docker network `br_dashboard` 存在，使用以下指令檢查。

```bash
docker network ls
```

The output should include a line similar to the following:

```bash
NETWORK ID     NAME           DRIVER    SCOPE
006dc6e8xxxx   br_dashboard   bridge    local
```

2. 若 docker network `br_dashboard` 不存在，請用以下指令建立：

```bash
docker network create --driver=bridge --subnet=192.168.128.0/24 --gateway=192.168.128.1  br_dashboard
```

3. 啟動 docker-compose：確保你在包含 docker-compose.yml 文件的目錄中。使用以下指令啟動 Airflow containers：

```bash
docker-compose up -d
```

   此指令將 containers 在背景啟動。檢查 Docker containers 的狀態，請使用：

4. 檢查 Docker 容器狀態：要驗證 Docker containers 是否正常運行，使用以下指令：

```bash
docker-compose ps
```

### 第四步：訪問 Airflow 網頁介面

Airflow 啟動後，打開瀏覽器並訪問 `http://localhost:8080`。

使用 `.env` 文件中的用戶名 `_AIRFLOW_WWW_USER_USERNAME` 和密碼 `_AIRFLOW_WWW_USER_PASSWORD` 登錄，預設值都是 airflow。

### 第五步: 設置必要的參數

在 Airflow 網頁介面中，你需要至少設定以下的參數，以確保 Airflow 正確運作。

在介面的 Admin -> Connections 中添加一個新的連線，預設值如下：

```
Connection Id: postgres_default
Connection Type: Postgres_default
Host: dashboard-data
Database: dashboard
Loging: airflow
Password: airflow
Port: 5432
```

> **i01**
> 連線的設定對應 `.env` 中的設定。Database 對應 `POSTGRES_DB`，Loging 對應 `POSTGRES_USER`，Password 對應 `POSTGRES_PASSWORD`。

在 Admin -> Variables 中添加兩個新的變數：

```
DEFAULT_EMAIL_LIST: ['your_email_1@mail', 'your_email_2@mail']
HTTPS_PROXY_ENABLED: false
PROXY_URL: {'https': '{ip}:{port}'}  # 不需要使用 proxy 則不用添加
```

> **i02**
> DEFAULT_EMAIL_LIST 是當資料流運行錯誤時所要寄送的郵件清單。若不需要使用此功能可隨意填寫 e-mail，若需要使用此功能請參考[官方文件](https://airflow.apache.org/docs/apache-airflow/2.5.1/howto/email-config.html)。

> **i03**
> HTTPS_PROXY_ENABLED 是設定 Airflow 是否需要透過 proxy 訪問外部網站。當設定為 false 時，全部資料流將無法透過 proxy 對外訪問；當設定為 true 時，可在個別資料流設定，透過 PROXY_URL 對外訪問。

> **w01**
> 如果你沒有臺北城市儀表板的範例 PostgreSQL 資料庫，可以按照以下步驟創建。

## 設置 PostgreSQL 數據庫

要設置範例 PostgreSQL 環境，請按照以下步驟操作：

### 第一步：修改 .env 文件

新增資料庫設定至目錄中的 `.env` 文件，完整內容如下:

 ``` bash
 AIRFLOW_IMAGE_NAME=myairflow:2.7.3
AIRFLOW_UID=50000
AIRFLOW_PROJ_DIR=../
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow

# postgres dashboard config
POSTGRES_DB=dashboard  # new add
POSTGRES_USER=airflow  # new add
POSTGRES_PASSWORD=airflow  # new add

# pgadmin config
PGADMIN_DEFAULT_EMAIL=default@gmail.com  # new add
PGADMIN_DEFAULT_PASSWORD=default  # new add
 ```

### 第二步：啟動 PostgreSQL 和 pgAdmin 容器

`docker-compose-db.yaml` 文件定義了兩個服務：分別為 PostgreSQL container（名為 dashboard-data）和 pgAdmin container。

> **i04**
> pgAdmin 是 PostgreSQL 的視覺化網頁介面。

要啟動這些容器，請使用以下指令：

``` bash
docker-compose -f docker-compose-db.yaml up -d
```

上述指令將會創建一個名為 `dashboard` 的資料庫，並默認 e-mail 是 `airflow`，密碼為 `airflow`。資料儲存於本地 volumes `./db-data`。

> **i05**
> 預設 e-mail 和 password 通過 `.env` 中的環境變量設置。

### 第三步：使用 pgAdmin 連接到 PostgreSQL

啟動成功後，可以透過瀏覽器輸入 `http://localhost:8889` 訪問 pgAdmin。

使用 `.env` 中指定的電子郵件（PGADMIN_DEFAULT_EMAIL）和密碼（PGADMIN_DEFAULT_PASSWORD）登錄。

在左側欄找到 `Servers`，右鍵點擊開啟並於 `Connection` 輸入以下資訊以創建資料庫。

```
Host name/address: dashboard-data
Port: 5432
Maintenance database: dashboard
Username: airflow
Password: airflow
```

### 第四步：從備份中恢復數據庫

於 pgAdmin 建立好資料庫連接後，從備份文件恢復數據庫。請按照以下步驟操作：

**_looks_one_** 在 pgAdmin 左側欄，右鍵單擊已連接的資料庫 `db:dashboard-data/dashbnoard`，選擇 `Restore`。

**_looks_two_** 上傳 `local-env/dashboard-init` 並選擇該文件進行備份資料復原。

**_looks_3_** 在 Restore 視窗中，將 Data Options 分頁中 Do not save 分類下的 Owner 開關點擊至右側位置，以排除設置物件所有權的命令。

**_looks_4_** 在 Restore 視窗中，將 Data Options 分頁中 Do not save 分類下的 Privileges 開關點擊至右側位置，以排除創建訪問權限的命令。

### 第五步：完成

資料復原過程完成後，你應該已經準備好臺北市資訊局團隊提供的 Airflow 運行所需的資料庫 schema。你可以在 pdAmin 介面中依次點開 dashboard-data -> Databases -> dashboard -> Schemas -> public -> Tables 查看所有表格，並透過 Airflow 網頁介面運行你的資料流。

