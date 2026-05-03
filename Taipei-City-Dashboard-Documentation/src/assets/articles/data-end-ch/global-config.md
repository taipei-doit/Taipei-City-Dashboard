

為了能夠快速在不同環境中部屬並且保護敏感資訊，本專案透過三種方式來記錄會使用到的全域設定：

**_looks_one_** 系統設定

**_looks_two_**  Airflow Connections

**_looks_3_**  Airflow Varialbes


## 系統設定

系統設定檔位於 `/config/dockerfile`。在一般開發過程中，不需要調整或深入瞭解此檔案，只需使用其中的環境變數來生成系統路徑。


## Airflow Connections

Airflow Connections 可以快速添加可連接的資料庫，相關設定已在[下載並設定專案](/data-end/project-setup)章節設置完成。

可以通過 Airflow 網頁介面，在上方的 Admin -> Connections 確認相關設定。

## Airflow Variables

Airflow Variables 用於記錄不應該 hardcode 在程式中的資訊，例如 API key、帳號、密碼、email等。

必要的資訊已在[下載並設定專案](/data-end/project-setup)章節設置完成，可以透過 Airflow 網頁介面查看相關設定。

以下是本專案用到的其他變數，若使用到相關的資料流請務必確保已添加，若無用到則不用添加。

| Key | Val | 說明 |
| -------- | -------- | -------- |
| CWA_API_KEY | your_key | 使用氣象資料開放平臺 API 需要的金鑰* |
| MOENV_API_KEY | your_key | 使用環境部環境資料開放平臺 API 需要的金鑰 |
| TDX_CLIENT_ID | your_tdx_clien_id | 使用 TDX 平台所需要的帳號* |
| TDX_CLIENT_SECRET | your_tdx_clien_secret | 使用 TDX 平台所需要的密碼 |

> **i01**
> [氣象資料開放平臺](https://opendata.cwa.gov.tw/index)是由中央氣象署(Central Weather Administration, CWA)建立，收錄了有關氣象、地震、天文等資料。

> **i02**
> [環境資料開放平臺](https://data.moenv.gov.tw/)是由環境部(Ministry of Environment, MOENV)建立，收錄了大氣、水文、汙染等資料。

> **i03**
> [運輸資料流通服務平臺](https://tdx.transportdata.tw/)(Transport Data eXchange, TDX)是由交通部建立，整合了交通、觀光等資料。

## 實際應用

為了方便開發者管理全域變數，本專案將所有使用到的全域變數集中在 `/dag/settings/global_config.py` 中。開發者可根據需求進行調整。
