

通用函式是將本專案頻繁使用的程式碼，抽出形成獨立的模組，並根據處理階段命名。所有通用函式可在 `/dags/utils` 找到。

下方列出常用的通用函式功能，便於快速查閱所需片段。

## 通用函式一覽

### 通用函式-生成建表 SQL

生成用來建表的 SQL。該 SQL 包含給定的資料欄位以及本專案標準表的 `_ctime`, `_mtime`, `ogc_fid` 欄位及適當的權限。[文章連結](/data-end/utils-generate-sql)。

> **i01**
> 本專案的標準表定義請參閱[資料流表格](/data-end/dag-table)

### 通用函式-抽取階段

包含下載、解壓縮、取得 data.taipei API、取得 data.taipei 檔案更新時間、取得 GeoJSON 的範例、取得 SHPfile 的範例、取得 KML/KMZ 的範例。[文章連結](/data-end/utils-extract)。

### 通用函式-轉換時間

包含處理民國年、標準化時間與時區、去除時間中有上下午中文的函式。[文章連結](/data-end/utils-transform-time)。

### 通用函式-轉換空間

包含三維 `Polygon` 轉成二維、`LineString` 轉成 `MultiLineString`、`Polygon` 轉成 `MultiPolygon`、將 x, y 座標轉為 `Point` 欄位、地理空間資訊轉成 WKBGeometry 格式。[文章連結](/data-end/utils-transform-geometry)。

### 通用函式-轉換地址

用於清洗、標準化、分解地址，建議適用於臺北市地址。[文章連結](/data-end/utils-transform-address)。

### 通用函式-儲存階段

將帶有地理資訊的表格或不帶地理資訊的表格存入資料庫。[文章連結](/data-end/utils-load)。

### 通用函式-取得 TDX token

取得 TDX 平台 token （需自行申請帳號）。[文章連結](/data-end/utils-tdx)。
