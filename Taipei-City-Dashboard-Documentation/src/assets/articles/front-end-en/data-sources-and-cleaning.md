## Main Data Sources of This Project
Data sources of this project should be from [data.taipei](https://data.taipei/) unless necessary. In certain cases, data from the central government or relevant organizations could be utilized. However, this project currently doesn’t accept or use any data from other local governments.

Government open data classification can be complicated or even messy at times. Often, the same dataset could be found on different platforms with slight differences in quality and content. To combat this issue, it is recommended to use data that is **closest to the actual source**. For example, data.taipei should be the primary source for all Taipei City related data and not the central government’s open data platform.

### Recommended Platforms
>**t01**
>If you are unable to find the dataset you require from any of the below platforms, you can try to contact the responsible department to obtain the data. Note that the requested data cannot include personal, illegal, or commercial information.

**Primary Sources**

[data.taipei (Taipei City 臺北市資料大平臺)](https://data.taipei/) ***verified***

[data.gov.tw (Central Government 政府資料開放平臺)](https://data.gov.tw/) ***verified***

[Transport Data eXchange (運輸資料流通服務平臺)](https://tdx.transportdata.tw/) ***verified***

**Other Sources**

[Open Weather Data (氣象資料開放平臺)](https://opendata.cwb.gov.tw/index) | [Environmental Information Open Platform (環境資料開放平臺)](https://data.epa.gov.tw/) | [Internet of Things for Water Resources (水資源物聯網入口網)](https://iot.wra.gov.tw/index.jsp) | [alerts.ncdr.nat.gov.tw (民生示警公開資料平台)](https://alerts.ncdr.nat.gov.tw/) | [Civil IoT Taiwan (民生公共物聯網)](https://ci.taiwan.gov.tw/dsp/) | [cpabm.cpami.gov.tw (全國建築管理資訊系統)](http://cpabm.cpami.gov.tw/OpenDataList.jsp) | [data.ly.gov.tw (立法院開放資料服務平台)](https://data.ly.gov.tw/) | [data.gcis.nat.gov.tw (商工行政資料開放平臺)](https://data.gcis.nat.gov.tw/main/index;jsessionid=864DC777726AA52FA5AD496EFBE6266B) | [Data Market (資料集平台)](https://scidm.nchc.org.tw/) | [tod.moea.gov.tw (經濟部主題式開放資料服務)](https://tod.moea.gov.tw/) | [cop.land.moi.gov.tw (地政整合資訊服務共享協作平台)](https://cop.land.moi.gov.tw/Portal/index.aspx) | [Open Data Services of MOC(文化資料開放服務網)](https://opendata.culture.tw/) | [CDC Open Data Portal (疾管署開放資料平台)](https://data.cdc.gov.tw/) | [data.fda.gov.tw (食品藥物開放資料平臺)](https://data.fda.gov.tw/) | [Public AgriData Exchange (行政院農業委員會資料開放平台)](https://data.coa.gov.tw/)

## Data Cleaning Recommendations
In general, when processing data, attention should be paid to whether the units are standardized, if there are obvious missing values, and if the data format is correct (e.g., numeric data should not be stored as strings). If the original dataset does not have unique identifiers for individual data points, they should be added during the processing. Below are more detailed explanations for three common data types in this project.

### Time
When processing data, special attention should be given to time-related information. First, the time zone of the data should be included in the time stamp, following the official format of this project, `YYYY-MM-DDThh:mm:ssTZD` (e.g., 2023-06-16T18:20:00+08:00). Additionally, the time of the data source's most recent update and its frequency, the time it was stored in the database, and the time it was modified in the database should be noted. However, the above time stamps can be temporarily omitted for static demos in this project.

### Geospatial
Pay special attention to the coordinate system used in geospatial data. Currently, this project only accepts data in the WGS84/EPSG:4326 format (e.g., longitude/latitude `[121.593444, 24.963627]`). If the original data is in a different format (e.g., the commonly used TWD97/EPSG:3826 format in the Taiwanese government), it must be converted to WGS84.

### Administrative Divisions
When processing administrative division data, it is important to check if the names contain less common Mandarin characters (e.g., 糖廍ㄅㄨˋ里). This may cause the database to have difficulty properly reading the administrative division names. In such cases, it is recommended to include English phonetic spelling or special annotations. Additionally, at the village level, there may be instances of the same name, so it is advisable to store village-level information along with the corresponding district name. This can be achieved by using another parameter to store it or concatenating the two values together (e.g., 大安區和安里).
