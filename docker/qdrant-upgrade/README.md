# 向量資料庫升級腳本

## 功能說明

此腳本用於將 PostgreSQL 資料庫中的資料轉換為向量嵌入，並上傳至 Qdrant 向量資料庫。

### 主要功能

1. 從 PostgreSQL 讀取 `query_charts` 和 `components` 表的資料
2. 使用 `intfloat/multilingual-e5-base` 模型生成多語言向量嵌入
3. 將向量資料上傳至 Qdrant 向量資料庫
4. 支援資料持久化（可選）

## 使用方式

### 1. 確保服務已啟動

首先啟動資料庫服務（包含 Qdrant）：

```bash
cd docker
docker compose -f docker-compose-db.yaml up -d
```

### 2. 執行向量升級

```bash
# 方式 1: 前景執行（可看到即時日誌）
docker compose --profile tools up vector-db-upgrade

# 方式 2: 背景執行
docker compose --profile tools up -d vector-db-upgrade

# 查看執行日誌
docker compose logs -f vector-db-upgrade

# 檢查執行狀態
docker compose ps vector-db-upgrade
```

### 3. 執行完成後

腳本執行完成後會自動停止容器。如需再次執行：

```bash
# 移除舊容器
docker compose rm -f vector-db-upgrade

# 重新執行
docker compose --profile tools up vector-db-upgrade
```

## 環境變數配置

在 `docker/.env` 檔案中配置以下變數：

### 資料庫連接

```env
# PostgreSQL 配置（使用與 dashboard-be 相同的配置）
DB_MANAGER_HOST=postgres-manager
DB_MANAGER_PORT=5432
DB_MANAGER_USER=your_db_user
DB_MANAGER_PASSWORD=your_db_password
DB_MANAGER_DBNAME=your_db_name
```

### Qdrant 配置

```env
# Qdrant 向量資料庫配置
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your_api_key
QDRANT_COLLECTION_NAME=query_charts
```

### 可選配置

```env
# Python 版本（預設 3.11）
PYTHON_IMAGE_TAG=3.11

# 向量資料輸出路徑（可選）
VECTOR_OUTPUT_CSV=/data/query_charts_vectors_mapping.csv
VECTOR_DATA_PATH=./data
```

## 資料結構

### 輸入資料（PostgreSQL）

腳本會執行以下 SQL 查詢：

```sql
	SELECT
		c.id,
		qc.index,
		c.name,
		qc.city,
		qc.long_desc,
		qc.use_case
	FROM query_charts qc
	INNER JOIN components c ON qc.index = c.index
	where id in (select distinct unnest(components) from dashboards d where id
	in (select distinct dashboard_id  from dashboard_groups dg where group_id  in (select distinct id from "groups" g where is_personal is false))
```

### 輸出資料（Qdrant）

每筆資料會包含：

- **id**: 資料唯一識別碼
- **vector**: 768 維向量嵌入
- **payload**:
  - `id`: 原始資料 ID
  - `index`: 索引值
  - `name`: 名稱
  - `city`: 城市
  - `long_desc`: 詳細描述
  - `use_case`: 使用案例

## 注意事項

1. **執行時間**: 根據資料量大小，執行時間可能需要數分鐘至數小時
2. **資源需求**: 建議至少 4GB RAM（模型載入需要約 2GB）
3. **網路連接**: 首次執行會下載 Sentence Transformer 模型（約 500MB）
4. **資料覆蓋**: 執行時會刪除並重建 `query_charts` collection

## 故障排除

### 無法連接資料庫

```bash
# 檢查資料庫服務狀態
docker compose -f docker-compose-db.yaml ps

# 檢查網路連接
docker network inspect br_dashboard
```

### Qdrant 連接失敗

```bash
# 檢查 Qdrant 服務
docker compose -f docker-compose-db.yaml logs qdrant

# 測試 Qdrant API
curl http://localhost:6333/collections
```

### 記憶體不足

在 `docker-compose.yaml` 中調整資源限制：

```yaml
vector-db-upgrade:
  deploy:
    resources:
      limits:
        memory: 6G
```

### 查看詳細錯誤

```bash
# 查看完整日誌
docker compose logs vector-db-upgrade

# 進入容器除錯
docker compose run --rm vector-db-upgrade sh
```

## 開發與測試

### 本地測試

```bash
# 安裝依賴
pip install pandas sentence-transformers qdrant-client sqlalchemy psycopg2-binary

# 設定環境變數
export DB_MANAGER_HOST=localhost
export DB_MANAGER_PORT=5432
export DB_MANAGER_USER=your_user
export DB_MANAGER_PASSWORD=your_password
export DB_MANAGER_DBNAME=your_db
export QDRANT_URL=http://localhost:6333
export QDRANT_API_KEY=your_key

# 執行腳本
python upgrade_vector_db.py
```

### 修改 SQL 查詢

編輯 `upgrade_vector_db.py` 中的查詢語句：

```python
query = """
    SELECT
        qc.id,
        qc.index,
        c.name,
        c.city,
        c.long_desc,
        c.use_case
    FROM query_charts qc
    INNER JOIN components c ON qc.index = c.index
    WHERE c.city = 'Taipei'  -- 自訂過濾條件
"""
```

## 相關文件

- [Qdrant 文件](https://qdrant.tech/documentation/)
