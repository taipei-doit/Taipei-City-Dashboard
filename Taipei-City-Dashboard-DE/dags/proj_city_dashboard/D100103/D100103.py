from airflow import DAG
from operators.common_pipeline import CommonDag

def D100103(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")

    # Extract
    # 20250818 來源api 改為csv檔案
    url = 'https://tsis.dbas.gov.taipei/statis/webMain.aspx?sys=220&ymf=9800&kind=21&type=0&funid=a05900201&cycle=4&outmode=12&compmode=0&outkind=1&deflst=2&nzo=1'
    ENCODING = 'utf-8-sig'
    raw_data = pd.read_csv(url, encoding=ENCODING)
    data = raw_data.copy()
    # Transform
    # Clean up year column
    data['year'] = data['統計期'].str.replace(r'[^\d]', '', regex=True)
    data["year"] = data["year"].apply(lambda x: int(x) + 1911)
    
    # Reshape from wide to long format
    # Create records for each gender category
    records = []
    
    for _, row in data.iterrows():
        year = row['year']
        
        # Total
        records.append({
            'year': year,
            'category': '總計',
            'parental_leave_count': row['就業保險育嬰留職停薪津貼初次核付人數[人]/ 總計']
        })
        
        # Male
        records.append({
            'year': year,
            'category': '男',
            'parental_leave_count': row['就業保險育嬰留職停薪津貼初次核付人數[人]/ 男']
        })
        
        # Female
        records.append({
            'year': year,
            'category': '女',
            'parental_leave_count': row['就業保險育嬰留職停薪津貼初次核付人數[人]/ 女']
        })
    
    # Create new dataframe from records
    data = pd.DataFrame(records)
    
    # Convert data types
    data["year"] = data["year"].astype(int)
    data["parental_leave_count"] = data["parental_leave_count"].astype(int)
    # Time
    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
    # Reshape
    ready_data = data.copy()

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=None,
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data["data_time"].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )


dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="D100103")
dag.create_dag(etl_func=D100103)
