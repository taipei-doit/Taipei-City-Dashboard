

> **w01**
> 請務必確認你已根據[下載並設定專案](/data-end/project-setup)章節部屬成功。

## 執行 DAG

打開瀏覽器並訪問 `http://localhost:8080` 進入 Airflow 網頁介面。

點選介面最上方列表的 DAGs 頁籤，可查看 DAG 列表與其執行狀況。

下方列表找到 `template_test`，點擊名稱左邊的按鈕，當按柳呈現藍色時即代表已啟動開 DAG。

點擊 DAG 名稱，可進入詳細的監控頁面，此時 DAG 應該已經自動運行中。

若沒有自動運行，可於頁面右上角找到播放按鈕，手動點擊並選擇 Trigger DAG，DAG 將被手動執行一次。

當頁面中的方格都呈現綠色，代表此次任務全部執行成功；若其中有紅色，可點擊該方格查看 log，並進行適當的除錯。


## 檢查資料

打開瀏覽器並訪問 `http://localhost:8889` 進入 pgAdmin，pgAdmin 是 PSQL 的圖形化介面，讓我們更容易使用 PSQL。

輸入帳號密碼進入後，你可以在 pgAdmin 的左側欄找到 server，點擊打開可查看 server 下的資料庫，打開資料庫下的 Schemas 的 Tables 就能查看所有表格。

找到 `db:dashboard/dashboard/heal_hospital` 點擊滑鼠右鍵，選擇 `View/Edit Data` 並選擇 `Last 100 Rows`，右邊視窗將顯示該表格最後一百筆資料。

透過下方卷軸拉動，查看該表格最右邊的欄位，欄位 `_mtime` 紀錄該筆資料被儲存的時間。若此資料是因剛才 DAG 執行成功儲存的，兩者時間將非常接近；若時間並不吻合，則有可能 DAG 執行成功，但資料並未被儲存。

> **i01**
> `_mtime` 是該列資料的最後修改時間，欄位說明可見上一章[資料流表格](/data-end/dag-table)。
