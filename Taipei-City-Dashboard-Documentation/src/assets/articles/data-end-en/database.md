

## PostgreSQL簡介

PostgreSQL 是一個開源的、物件關聯(object-relational)的結構化資料庫。本專案選用 PSQL 的原因除了開源以外，也因為本專案有大量的地理空間資料，PSQL 的擴充工具 Postgis 很好的支援此特點。

## 資料端資料庫結構

資料端所用到的所有資料，都位於 `db:dashboard` 當中。

### airflow

PSQL 中的 `db:dashboard/airlfow` 記錄 Airflow 運行所需要的 metadata, log 等。

### dashboard

PSQL 中的 `db:dashboard/dashboard` 記錄臺北城市儀表板需要的所有應用資料。資料可以被後端使用 SQL 提取及統計，或是被 Geoserver 轉換為圖磚，最後供前端使用。

> **i01**
> 後端相關文件可參閱[這裡](https://tuic.gov.taipei/documentation/back-end/introduction)。

> **w01**
> 我們的 Geoserver 相關設定尚未開源。因此，目前外部開發者我們建議使用 Mapbox 等替代地圖服務，或直接在前端中儲存 GeoJSON 文件。
