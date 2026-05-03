

## 開發環境

為了最佳的開發體驗，我們建議使用作業系統為 Windows 或 macOS 的電腦。

### 開發工具

請確保你的電腦上有安裝了以下開發工具：
Python（建議額外安裝 Anaconda）、Git（可以額外安裝 GitHub Desktop）、Visual Studio Code。

### 程式編輯器

Visual Studio Code（後稱 VSCode）是我們首選的程式編輯器。我們建議安裝以下擴充工具以提升開發效率：
Python、Docker、Python Extension Pack、Python Debugger、pylint、black formater、indent-rainbow、isort。

## 技術塔

### Airflow

Airflow 是一個Python寫的工作流管理系統(Workflow Management System)。本專案使用Airflow排程與監控工作流。 Airflow 的官方網站可以在[這裡](https://airflow.apache.org/)找到。

### PostgreSQL

本專案使用 PostgreSQL 作為資料庫。PostgreSQL 的官方網站可以在[這裡](https://www.postgresql.org/)找到。

### Python

Python 是本專案的主要程式語言。Python 的文件和安裝指南可以在[這裡](https://www.python.org/)找到。
本專案使用的 Python 版本為 3.8，使用套件可以在下章節[下載並設定專案](/data-end/project-setup)完成後，於本專案路徑的`/requirements.txt`找到。
其中幾個關鍵的套件說明如下：

### Pandas

Pandas 是用來在 Python 中向量化處理資料與分析的套件，本專案使用 Pandas 來處理大部份的結構化資料。官方文件可以在[這裡](https://pandas.pydata.org/)找到。

### GeoPandas

GeoPandas 是基於 Pandas 的資料型態，用以處理地理空間(geospatial)資料的套件。官方文件可以在[這裡](https://geopandas.org/en/stable/index.html#)找到。

### SQLAlchemy

SQLAlchemy 是用以在 Python 中使用 ORM(Object Relational Mapper)與 SQL 互動的工具(toolkit)。本專案使用 SQLAlchemy 作為與資料庫連接的套件，官方文件可以在[這裡](https://www.sqlalchemy.org/)找到。