from airflow import DAG
from operators.common_pipeline import CommonDag

def D100104_2(**kwargs):
    '''
    Service applicant count per year of maternity hospitals service from data.taipei.

    Explanation:
    -------------
    total_count: There are many columns in original data, we only keep the column 
    `生育健康篩檢補助/總計[人次]` as representative.
    '''
    from utils.extract_stage import get_data_taipei_api
    import pandas as pd
    from utils.transform_time import convert_str_to_time_format
    from utils.extract_stage import get_data_taipei_file_last_modified_time
    from utils.load_stage import save_dataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine

    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    # raw_data_db_uri = kwargs.get('raw_data_db_uri')
    # data_folder = kwargs.get('data_folder')
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    # proxies = kwargs.get('proxies')
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    page_id = 'a14dd58c-ecef-480c-b574-889ecfa631c3'
    # Manually set
	# 資料來源異動
    url = 'https://tsis.dbas.gov.taipei/statis/webMain.aspx?sys=220&ymf=10400&kind=21&type=0&funid=a05041801&cycle=4&outmode=12&compmode=0&outkind=1&deflst=2&nzo=1'
    # Extract
    ENCODING = 'utf-8-sig'
    raw_data = pd.read_csv(url, encoding=ENCODING)

    # Transform
    # Rename
    data = raw_data.copy()
    keep_col = ['統計期', '生育健康篩檢補助/總計[人次]']
    data = data[keep_col]
    col_map = {
        '統計期': 'year',
        '生育健康篩檢補助/總計[人次]': 'total_count'
    }
    data = data.rename(columns=col_map)
    # Transfer year from ROC to AD
    data['year'] = data['year'].replace('年', '', regex=True)
    data['year'] = data['year'].astype(int) + 1911
    # Time
    data['data_time'] = get_data_taipei_file_last_modified_time(page_id)
    data['data_time'] = convert_str_to_time_format(data['data_time'])
    # Reshape
    ready_data = data.copy()

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine, data=ready_data, load_behavior=load_behavior,
        default_table=default_table, history_table=history_table,
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data['data_time'].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='D100104_2')
dag.create_dag(etl_func=D100104_2)
