from airflow import DAG
from operators.common_pipeline import CommonDag



def _transfer(**kwargs):
    '''
    Service applicant count per year of Sea Sand House Registry statistics from data.taipei.

    Explanation:
    -------------
    `年底別` as year
    `列管件數/總計[件]` as total_cases
    `列管件數/須拆除重建[件]` as cases_need_reconstruction
    `列管件數/可加勁補強[件]` as cases_can_be_reinforced.
    `列管戶數/總計[戶]` as total_households.
    `列管戶數/須拆除重建[戶]` as households_need_reconstruction.
    `列管戶數/可加勁補強[戶]` as households_can_be_reinforced.
    
    '''
    import pandas as pd
    from utils.load_stage import save_dataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine
    from utils.get_time import get_tpe_now_time_str

    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    # raw_data_db_uri = kwargs.get('raw_data_db_uri')
    # data_folder = kwargs.get('data_folder')
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    
    # 20250818 來源api 改為csv檔案
    url = 'https://tsis.dbas.gov.taipei/statis/webMain.aspx?sys=220&ymf=10600&kind=21&type=0&funid=a05042701&cycle=4&outmode=12&compmode=0&outkind=1&deflst=2&nzo=1'
    ENCODING = 'utf-8-sig'
    raw_data = pd.read_csv(url, encoding=ENCODING)


    # Transform
    # Rename
    data = raw_data.copy()
    col_map = {
        "統計期": "year",
		"列管件數/總計[件]": "total_cases",
		"列管件數/須拆除重建[件]": "cases_need_reconstruction",
		"列管件數/可加勁補強[件]": "cases_can_be_reinforced",
		"列管戶數/總計[戶]": "total_households",
		"列管戶數/須拆除重建[戶]": "households_need_reconstruction",
		"列管戶數/可加勁補強[戶]": "households_can_be_reinforced"

    }
    data = data.rename(columns=col_map)
    # Transfer year from ROC to AD
    data['year'] = data['year'].replace('年', '', regex=True)
    data['year'] = data['year'].astype(int) + 1911
    # Time

    data["data_time"] = get_tpe_now_time_str(is_with_tz=True)

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

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='sea_sand_houses_tpe')
dag.create_dag(etl_func=_transfer)
