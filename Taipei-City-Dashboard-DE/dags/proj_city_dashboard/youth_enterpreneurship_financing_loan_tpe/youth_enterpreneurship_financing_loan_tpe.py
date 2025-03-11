from airflow import DAG
from operators.common_pipeline import CommonDag
from utils.extract_stage import get_data_taipei_api
import pandas as pd
from utils.transform_time import convert_roc_date
from utils.load_stage import save_dataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
from sqlalchemy import create_engine
from utils.get_time import get_tpe_now_time_str


def _transfer(**kwargs):
    '''
    Service applicant count per year of Sea Sand House Registry statistics from data.taipei.

    Explanation:
    -------------
    `期間(年月)` as period
    `申請件數－累計` as total_cases
    `核准件數－累計` as total_approvals
    `核准金額－累計－萬元` as total_approved_amount_ten_thousand_ntd.
    '''


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
    # Manually set
    rid = '6e66d5ea-250e-4078-ac99-6247973a0ddd'
    page_id = '8d7527ee-1998-4101-9f96-6fe60137c266'

    # Extract
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_tpe_now_time_str()
 
    # Transform
    # Rename
    data = raw_data
    col_map = {
        "期間": "period",
        "申請件數－累計": "total_cases",
        "核准件數－累計": "total_approvals",
        "核准金額－累計－萬元": "total_approved_amount_ten_thousand_ntd"
    }
    data = data.rename(columns=col_map)
    data['period'] = data['period'].apply(convert_roc_date)

    # Time
    # standardize time
    data = data.drop(columns=['_id','_importdate'])
    # Reshape
    ready_data = data.copy()

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine, data=ready_data, load_behavior=load_behavior,
        default_table=default_table
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data['data_time'].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='youth_enterpreneurship_financing_loan_tpe')
dag.create_dag(etl_func=_transfer)
