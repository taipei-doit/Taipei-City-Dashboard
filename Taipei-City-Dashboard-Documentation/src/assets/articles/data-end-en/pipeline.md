

本專案使用 Airflow 監控與排程資料流，有關 Airflow 的基本概念可參考[官方文件](https://airflow.apache.org/docs/apache-airflow/stable/index.html)，以下說明將假設開發者已具備基本的 Airflow 知識。

如[撰寫Python程式碼](/data-end/dag-code)章節所示，本專案使用自製的 pipeline 來隱藏程式與 Airflow 互動的細節。本章將說明我們所使用的 `common_pipeline` 的設計理念與程式。


## 標準的 Airflow DAG

官方文件中示範的 pipeline 可以在[這裡](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/fundamentals.html#example-pipeline-definition)查看。開發者需要對 DAG 設定許多參數，然後利用不同的 `operator` 建構 `task`，最後將這些 `task` 組成 `pipeline`。


## 本專案的 pipeline

### 設計

本專案的 pipeline 可在 `dags\operators\common_pipeline.py` 找到，有以下特點：

**_looks_one_** 著重在資料處理而不是系統

相較於一個完善的 Airflow 專案，我們希望優先讓這個專案成為一個開放資料處理的匯合處，鼓勵更多人貢獻。

**_looks_two_** 盡可能降低門檻

本專案預想的開發者主要是分析人員，他們會寫 Python，但對 Airflow 不了解，也不熟悉軟體工程。他們在研究或工作中使用開放資料並對資料進行處理。我們希望這些開發者只需少量修改即可貢獻程式碼，讓其他人無需再造輪子。

**_looks_3_** 減少與 Airflow 耦合

Airflow 是排程與監控的平台，而不是資料處理本身。因此，本專案將 ETL 過程全部明示於一個檔案中，每個 DAG 彼此獨立。資料處理者可以輕鬆擷取片段程式碼，而不必然需要安裝 Airflow 來處理資料。

**_looks_4_** 隱藏與 Airflow 的互動

大部分資料處理非常簡單，直接撰寫 Airflow 互動的程式碼會顯得冗長且不必要。因此，本專案透過 `common_pipeline` 與 `job_config.json` 完成相關設定，使開發者能專注於資料處理。

**_looks_5_** 只使用 Python Operator

根據[這篇文章](https://medium.com/bluecore-engineering/were-all-using-airflow-wrong-and-how-to-fix-it-a56f14cb0753)的經驗，本專案不使用 Airflow 的多種 operator，而是全部使用 Python operator。這樣不僅減少了學習 operator 的成本，也避免了 operator 出錯時的除錯麻煩。


### code說明

由於實際程式碼篇幅較長，請至 `dags\operators\common_pipeline.py` 查看原始碼，或查看 [GitHub連結]()。為了方便理解，說明將從程式碼下方往上閱讀。

此 `pipeline` 總共有四個 `task` 如 246 行所示：

``` python
get_and_validate_config >> etl >> update_dataset_info >> dag_execution_success
```

**_looks_one_** task `get_and_validate_config`，讀取DAG設定檔，也就是前面文件所教學的 `jon_config.json` 內容。

**_looks_two_** task `etl` 代入各種設定，實際執行資料處理。此步驟所執行的內容並不在 `common_pipeline.py`，而是[撰寫Python程式碼](/data-end/dag-code)章節所示範的，一般情況所需開發的每個 DAG 獨立的 ETL 程式碼。

**_looks_3_** task `update_dataset_info` 將 `jon_config.json` 中的 `data_infos` 部分更新至 `db:dashboard/dashboard/dataset_info`。

**_looks_4_** task `dag_execution_success` 僅用來表示 DAG 已完成，無任何作用。


這四個 `task` 的 `operator` 定義於 222~243 行：

``` python
        with dag:
            get_and_validate_config = DummyOperator(task_id='get_job_config')
            
            etl = PythonOperator(
                task_id='etl',
                python_callable=etl_func,
                op_kwargs={
                    'dag_infos': dag_infos,
                    'raw_data_db_uri': self.raw_data_db_uri,
                    'ready_data_db_uri': self.ready_data_db_uri,
                    'proxies': self.proxies,
                    'data_path': self.data_path,
                }
            )

            update_dataset_info = PythonOperator(
                task_id='update_dataset_info',
                python_callable=_create_or_update_dataset_info,
                op_kwargs={'psql_uri': self.ready_data_db_uri, 'config': self.config}
            )

            dag_execution_success = DummyOperator(task_id='dag_execution_success')
```

行 204~219 則設定了 `pipeline` 的參數：

``` python
    def create_dag(self, etl_func=_etl_func_missing):
        dag_infos = self.config['dag_infos']
        data_infos = self.config['data_infos']
        default_args = dag_infos['default_args']
        default_args['email'] = self.fetch_email_list(default_args.get('email', []))

        # Create Pipeline
        dag = DAG(
            dag_id=dag_infos['dag_id'],
            default_args=default_args,
            start_date=datetime.strptime(dag_infos['start_date'], '%Y-%m-%d'),
            schedule_interval=dag_infos['schedule_interval'],
            tags=dag_infos['tags'],
            catchup=dag_infos['catchup'],
            description=dag_infos['description']
        )
```

task `get_and_validate_config` 雖使用 `DummyOperator` 無實際內容，但這個步驟實際作用於 class 初始化的時候，如行 148~169：

``` python
class CommonDag:
    ...
        def __init__(self, proj_folder, dag_folder):
        self.data_path = self.DATA_PATH
        self.dag_path = os.path.join(self.DAG_PATH, proj_folder, dag_folder)
        self.config = _read_config(self.dag_path)
        _validate_config(self.config)
        
        if Variable.get('HTTPS_PROXY_ENABLED', 'false').lower() == 'true':
            proxies = literal_eval(Variable.get('PROXY_URL'))
            self.proxies = {'http': proxies['https'], 'https': proxies['https']}
        else:
            self.proxies = None
        self.raw_data_db_uri = PostgresHook(
            postgres_conn_id=self.config['dag_infos']['raw_data_db']
        ).get_uri()
        self.ready_data_db_uri = PostgresHook(
            postgres_conn_id=self.config['dag_infos']['ready_data_db']
        ).get_uri()
```

其中使用到的函式 `_read_config` 與 `_validate_config` 定義於 class 之外的行 17~51：

``` python
def _read_config(path, file_name='job_config.json'):
    ...
    return config_dict


def _validate_config(config_dict):
    ...
    print('Validate config successfully.')
```

task `_create_or_update_dataset_info` 函式定義於行 84~145。

``` python
def _create_or_update_dataset_info(psql_uri, config):
    ...
    conn.close()
```

行 55~81，是當開發者忘記傳入 `etl_function` 的時候，能跳出 RuntimeError 並給予適當的提示。

``` python
def _etl_func_missing():
    ...
    raise RuntimeError(error_message)
```

最後，行 172~201 的 `fetch_email_list`函式，是為了靈活的使用 e-mail 群組。函式會比對 `job_config.json` 的`mail 參數與 Airflow Variables 是否有符合的關鍵字。

``` python
    def fetch_email_list(self, mail_list: list):
        ...
        return list(set(origin_mail_list))
```

> ** i01 **
> e-mail 群組功能如何被使用，請參考[撰寫DAG設定](/data-end/dag-config)章節最下方，說明 mail 參數部分。
