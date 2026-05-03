

## 在開發之前

資料處理是根據原始資料和目標進行適當的處理。在開始開發之前，強烈建議先徹底瞭解資料的特性，這將有助於有效規劃開發內容。

> **i01**
> 資料處理的目的是為了使其他人能夠進行後續應用。適當地紀錄資料中的業務知識也有助於未來的應用。

## 資料清單


以下表格為本專案整理，認為有助於釐清資料特性並需要紀錄的訊息。若其中涉及到程式碼、系統或是開發者不確定該採用何種命名方式，本專案建議採用 Python 常用的[snake_case](https://en.wikipedia.org/wiki/Snake_case)風格命名，即小寫英文字母並以下底線分隔單詞。

(部分資料欄位標示 `*`，將在下方補充說明。)

| 資料欄位 | 範例值 |
| -------- | -------- |
| 資料流名稱 | template_dag |
| 中文資料名 | 臺北市醫院清冊 |
| 英文資料名 | Hospital List in Taipei |
| 來源平台 | data.taipei |
| 資料權屬機關/平台* | 臺北市衛生局 |
| 來源資料說明文件 | https://data.taipei/dataset/detail?id=ffdd5753-30db-4c38-b65f-b77892773d60 |
| 來源位置 | https://data.taipei/api/v1/dataset/04a3d195-ee97-467a-b066-e471ff99d15d?scope=resourceAquire |
| 來源傳輸格式* | JSON |
| 來源資料範圍* | snapshot |
| 來源更新頻率 | Monthly |
| 是否包含敏感資訊 | False |
| 備註 |  |
| 維護方式* | current+history |
| Airflow 更新頻率 | Monthly |
| DB Table Name* | heal_hospital |
| DB Primary Key |  |
| DB Index |  |

本專案資料清單可以在[這裡](https://iimahow.notion.site/6e696d7dd8154461b6fe7872d8d5c83f?v=48a89c853ba040a5aed715cc4e6fb4b9&pvs=4)找到。


### *資料權屬機關/平台

不建議追溯資料最原始的來源，僅紀錄接觸到的來源。例如資料來自於TDX平台，相關資料可能來自地方政府。釐清資料源頭常常過於複雜，建議僅紀錄來自TDX即可。

### *來源傳輸格式

例如 XLSX, CSV, SHP, JSON, GeoJSON, TXT, XML, KML, KMZ 等......

### *來源資料範圍

或稱資料的跨福，本專案建議可用 `snapshot`, `new event`, `slice window`, `full history` 其中一種表示。

**_looks_one_** `snapshot`: 資料為某一個瞬間的狀態，例如當下的路燈分布。

**_looks_two_** `new event`: 資料僅包含新資訊（與歷史資訊互斥），例如新增加的交易。

**_looks_3_** `slice window`: 資料為為一段會變動時間的資訊，例如近三小時的天氣預報。

**_looks_4_** `full history`: 資料包含所有歷史至今的資料，例如過去至今所有的隨機強盜案件。

### *維護方式

維護方式是根據資料來源範圍不同，所制定的不同儲存方式，但具體方式應根據具體情況權衡。維護方式必須為 `append`, `replace`, `current+history` 三者的其中一個。`append` 是將資料無條件新增至指定表格；`replace` 是將指定表格 truncate 後，再新增資料；`current+history` 共有兩個目的地，其一為 current 表，另一張為 history 表。分別對 current 表執行上面的 replace 操作，再對 history 表執行 append 操作。

> **i02**
> `current+history` 的設計，是為了同時滿足快速與留存歷史資料。例如 YouBike 站點狀態雖然只呈現當下的即時資料，但我們留存所有歷史資料以供未來分析應用。長期下來，歷史資料會變得冗餘而查詢時間過長；因此另存 current 表，只留最後一次的資料，快速回應前端需求。

### *DB Table Name

建議命名規則為 `<dept>_<data name>`，`dept` 為資料平台或來源局處等，可方便記憶與分類之標籤。不使用應用主題分類，是因為一個資料常常有多種應用主題，應用主題也很可能會修改。

> **i03**
> 若資料來源為臺北市局處，可參考[臺北市各局處英文簡寫](https://iimahow.notion.site/a1f32a90110540368c5649da2b58701f?pvs=4)。
