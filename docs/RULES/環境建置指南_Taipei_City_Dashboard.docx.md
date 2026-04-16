**Taipei City Dashboard**

**本機開發環境建置指南**

2026 雙北程式設計節黑客松 — 資料工程師專用

# **0\. 前置需求**

執行前請確認以下軟體已安裝：

| Docker Desktop | 已安裝並啟動（工具列右下角有鯨魚圖示） |
| :---- | :---- |
| **Git** | git \--version 可正常輸出版本號 |
| **Node.js** | v18 以上（node \-v 可正常輸出） |
| **PowerShell** | 以系統管理員身份執行 |

⚠ 所有指令請在 PowerShell（系統管理員）中執行。

# **1\. 清理舊環境**

若是全新安裝，可跳過此步驟。若有舊的 container 或舊資料夾，執行以下指令：

### **1.1 停止並清除 Docker 舊容器與 Image**

docker compose down \-v \--remove-orphans  
docker image prune \-a

### **1.2 刪除舊資料夾（依實際路徑修改）**

Remove-Item \-Recurse \-Force "C:\\Users\\user\\Documents\\黑客松\\Taipei-City-Dashboard"

⚠ 若路徑不存在會顯示錯誤，可忽略，直接進行下一步。

# **2\. Clone 完整 Repo**

cd "C:\\Users\\user\\Documents\\黑客松"  
git clone https://github.com/taipei-doit/Taipei-City-Dashboard.git  
cd Taipei-City-Dashboard  
git checkout develop

Clone 完成後目錄結構如下：

Taipei-City-Dashboard/  
  Taipei-City-Dashboard-BE/   \# 後端 (Go)  
  Taipei-City-Dashboard-DE/   \# 資料工程 (Airflow)  
  Taipei-City-Dashboard-FE/   \# 前端 (Vue)  
  docker/                     \# 統一 docker compose  
  db-sample-data/             \# 範例資料

# **3\. 複製競賽設定檔**

將競賽提供的三個檔案複製到正確位置（依實際位置修改 $src）：

$de  \= "C:\\Users\\user\\Documents\\黑客松\\Taipei-City-Dashboard\\Taipei-City-Dashboard-DE"  
$src \= "C:\\Users\\user\\Downloads"   \# 依實際位置修改

Copy-Item "$src\\common\_pipeline.py" "$de\\dags\\operators\\common\_pipeline.py"  
Copy-Item "$src\\template\_dag.py"    "$de\\dags\\template\_dag.py"  
Copy-Item "$src\\job\_config.json"    "$de\\dags\\job\_config.json"

⚠ 若找不到檔案，用以下指令搜尋：Get-ChildItem \-Path C:\\Users\\user \-Recurse \-Filter template\_dag.py 2\>$null

# **4\. 啟動前端、後端與資料庫服務**

### **4.1 建立 Docker 網路**

docker network create br\_dashboard

### **4.2 建立 .env 設定檔**

cd "C:\\Users\\user\\Documents\\黑客松\\Taipei-City-Dashboard\\docker"  
Copy-Item ".env.template" ".env"  
notepad .env

在記事本中填入以下內容後存檔：

DB\_DASHBOARD\_USER=postgres  
DB\_DASHBOARD\_PASSWORD=postgres  
DB\_DASHBOARD\_DBNAME=dashboard  
DB\_MANAGER\_USER=postgres  
DB\_MANAGER\_PASSWORD=postgres  
DB\_MANAGER\_DBNAME=dashboard\_manager

其他 API key 欄位留空即可。

### **4.3 安裝前端套件（Linux 環境）**

docker run \--rm \\  
  \-v "C:\\Users\\user\\Documents\\黑客松\\Taipei-City-Dashboard\\Taipei-City-Dashboard-FE:/app" \\  
  \-w /app \\  
  node:21.6.0-alpine3.18 \\  
  npm install \--registry https://registry.npmmirror.com

⚠ 必須用 Docker 內的 Linux 環境安裝，在 Windows 安裝的 node\_modules 會導致 SIGBUS 錯誤。

### **4.4 啟動服務**

cd "C:\\Users\\user\\Documents\\黑客松\\Taipei-City-Dashboard\\docker"  
docker compose up \-d

⚠ 若出現 container name conflict，執行：docker rm \-f \<container名稱\> 後再重試。

### **4.5 初始化資料庫**

docker compose \-f docker-compose-db.yaml up \-d

⚠ 若出現 redis conflict：docker rm \-f redis，再重執行上方指令。

docker compose \-f docker-compose-init.yaml up

等待 exited with code 0 出現後，重啟後端：

docker restart dashboard-be

驗證前端正常：開啟瀏覽器 http://localhost

# **5\. 啟動 Airflow（DE 模組）**

### **5.1 建立 Airflow 資料庫**

docker exec postgres-data psql \-U postgres \-c "CREATE DATABASE airflow;"

### **5.2 建立 Airflow .env**

$env\_content \= @"  
AIRFLOW\_UID=50000  
USERNAME=airflow  
PASSWORD=airflow  
MATADATA\_DATABASE=postgresql+psycopg2://postgres:postgres@postgres-data:5432/airflow  
CELERY\_RESULT\_BACKEND=db+postgresql://postgres:postgres@postgres-data:5432/airflow  
REDIS\_CONN=redis://redis:6379/0  
"@

$env\_content | Out-File \-FilePath "C:\\Users\\user\\Documents\\黑客松\\Taipei-City-Dashboard\\Taipei-City-Dashboard-DE\\docker\\develop\\.env" \-Encoding utf8 \-NoNewline

### **5.3 將 Airflow 加入共用網路**

在 docker-compose.yaml 最底部新增：

$network\_config \= @"

networks:  
  default:  
    external: true  
    name: br\_dashboard  
"@

Add-Content \-Path "C:\\Users\\user\\Documents\\黑客松\\Taipei-City-Dashboard\\Taipei-City-Dashboard-DE\\docker\\develop\\docker-compose.yaml" \-Value $network\_config

### **5.4 修改 Airflow Webserver Port**

(Get-Content "...\\docker\\develop\\docker-compose.yaml") \-replace '"8080:8080"', '"8090:8080"' | Set-Content "...\\docker\\develop\\docker-compose.yaml"

⚠ 完整路徑：C:\\Users\\user\\Documents\\黑客松\\Taipei-City-Dashboard\\Taipei-City-Dashboard-DE\\docker\\develop\\docker-compose.yaml

### **5.5 啟動 Airflow**

cd "C:\\Users\\user\\Documents\\黑客松\\Taipei-City-Dashboard\\Taipei-City-Dashboard-DE\\docker\\develop"  
docker compose up \-d

### **5.6 建立 Airflow 管理員帳號**

docker exec \-it develop-airflow-webserver-1 airflow users create \--username airflow \--password airflow \--firstname Air \--lastname Flow \--role Admin \--email airflow@example.com

### **5.7 設定 Airflow Variables**

開啟 http://localhost:8090/airflow-sit，登入後前往 Admin → Variables → 新增：

| Key | DEFAULT\_EMAIL\_LIST |
| :---- | :---- |
| **Value** | \[\] |

### **5.8 設定 Airflow Connection**

前往 Admin → Connections → 新增：

| Connection Id | postgres\_default |
| :---- | :---- |
| **Connection Type** | Postgres |
| **Host** | postgres-data |
| **Database** | dashboard |
| **Login** | postgres |
| **Password** | postgres |
| **Port** | 5432 |

# **6\. 服務總覽**

| 服務 | URL | 帳密 |
| :---- | :---- | :---- |
| 前端 FE | http://localhost | \- |
| 後端 BE API | http://localhost:8088 | \- |
| Airflow | http://localhost:8090/airflow-sit | airflow / airflow |
| PostgreSQL | localhost:5432 | postgres / postgres |
| pgAdmin | http://localhost:5050 | 依 .env 設定 |

# **7\. 常見問題排除**

### **port 8080 already allocated**

查詢佔用的 container：  
docker ps \--format "table {{.Names}}\\t{{.Ports}}" | findstr 8080  
docker rm \-f \<container名稱\>

### **dashboard-fe SIGBUS / vite not found**

代表 node\_modules 是在 Windows 環境安裝的，需刪除並在 Docker 內重裝：  
Remove-Item \-Recurse \-Force "...\\Taipei-City-Dashboard-FE\\node\_modules"  
再執行步驟 4.3 的 docker run 指令。

### **Airflow: database airflow does not exist**

docker exec postgres-data psql \-U postgres \-c "CREATE DATABASE airflow;"

### **Airflow: postgres-data hostname not found**

Airflow 和 postgres-data 網路不通，確認 docker-compose.yaml 已加入步驟 5.3 的網路設定。

### **DAG 不出現**

檢查 .airflowignore，tutorial/ 資料夾被排除。DAG 請放在 proj\_city\_dashboard/ 或 proj\_new\_taipei\_city\_dashboard/ 下。  
