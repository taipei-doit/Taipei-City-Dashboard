

## Airflow 簡介

Airflow 是一個開源的、使用 Python 語言的、以批次導向的、可以排程與監控工作流的平台。官方文件可以在[這裡](https://airflow.apache.org/docs/apache-airflow/stable/index.html)找到。

## Airflow架構

Airflow 不僅僅是一個排程工具，而是一個完整的平台。平台總共由四個組件組成，包含 scheduler and executor、webserver、DAG files、metadata database。

具體而言，開發者撰寫 DAG files，scheduler 根據 metadata 驅動 executor 執行。執行的過程與成果可於 Airflow 網頁介面查看。詳細組件作用可參閱[官方文件](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html#airflow-components)。

> **i01**
> Airflow 將一個工作流的實體(instance)稱為一個有向無環圖(Directed Acyclic Graph, DAG) 。
> 在本專案中，一個 DAG 是一個資料取得到儲存的完整過程。一個 DAG 只應該取得一個資料源，可以儲存至一個或多個目的地。


## 資料夾結構

本專案資料夾結構與功用如下方所示：

```
├── dags
│   ├── operators                           // pipeline
│   │
│   ├── proj_city_dashboard                 // 台北城市儀表板現存之開放資料資料流
│   │   ├── D030101_1                       // 單一 DAG
│   │   │   ├── job_config.json             // DAG 設定檔
│   │   │   └── D030101_1.py                // DAG 程式碼
│   │   ├──  ...                            // 其餘 DAG
│   │
│   ├── proj_new_taipei_city_dashboard      // 新北市儀表板現存之開放資料資料流
│   │   ├── dependency_ratio_and_aging_index// 單一 DAG
│   │   │   ├── job_config.json             // DAG 設定檔
│   │   │   └── dependency_ratio_and_aging_index.py  // DAG 程式碼
│   │   ├──  ...                            // 其餘 DAG
│   │ 
│   ├── settings
│   │   └── global_config.py                // 全域設定
│   │ 
│   ├── tutorial                            
│   │   └── simple_template                 
│   │       ├── job_config.json             // 示範 DAG 設定檔
│   │       └── template_dag.py             // 示範 DAG 程式碼
│   │ 
│   └── utils                               // 通用函式
│       ├── opendata                        // 地址處理通用函式所需資料
│       │   └── ...             
│       ├── preprocess                      // 地址處理通用函式所需資料
│       │   └── ...        
│       ├──  transform_address.py           // 地址處理通用函式
│       ├──  ...                            // 其餘通用函式
│
├── data                                    // 暫存資料
├── local_env                               // 本地設定
└── Readme.md
```
