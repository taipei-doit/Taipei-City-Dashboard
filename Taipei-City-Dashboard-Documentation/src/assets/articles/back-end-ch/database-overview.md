## 簡介

此專案使用兩個 PostgreSQL 資料庫。第一個 (`dashboard`) 存儲儀表板組件的統計、歷史和空間資料。第二個 (`dashboardmanager`) 存儲臺北城市儀表板的用戶資訊、角色、權限群組、儀表板配置、組件配置等。

如果您還未完成資料庫初始化與設定，請參考[專案設置指南](/back-end/project-setup)。

## dashboard

`dashboard` 資料庫連接到 [Airflow](https://airflow.apache.org/)。資料庫中也預先安裝了 Postgis 擴充工具以支援地理座標資料。

這個資料庫的資料主要透過兩種方法提取。首先透過儀表板的後端，使用 SQL 提取統計和歷史資料。其次透過 [Geoserver](https://geoserver.org/)，負責提取和暫存空間資料並將其轉換為圖磚。

> **w01**
> 我們的 Airflow 相關設定尚未開源。因此，目前外部開發者應手動或透過其他服務將資料填充到 `dashboard` 資料庫中。

> **w02**
> 我們的 Geoserver 相關設定尚未開源。因此，目前外部開發者我們建議使用 Mapbox 等替代地圖服務，或直接在前端中儲存 geojson 文件。在[這個文章中](/front-end/map-data)可以了解更多。

## dashboardmanager

`dashboardmanager` 資料庫連接到儀表板的後端。這份文件將在[下一章](/back-end/users-roles-groups-db)更深入地介紹本專案資料庫的架構以及如何使用。