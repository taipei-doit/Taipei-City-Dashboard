from airflow import DAG
from operators.common_pipeline import CommonDag

def _transfer(**kwargs):
    '''
    Service applicant count per year of Sea Sand House Registry statistics from data.taipei.

    Explanation:
    -------------
    `年度` as year
    `查核家數`as audited_households
    `節電量－萬度/年`as power_saving_ten_thousand_kWh_per_year
    `減碳量－公噸`as carbon_reduction_metric_tons
    `不合格家數`as non_compliant_households
    `合格率` as compliance_rate
    `複查合格率` as reinspection_compliance_rate
    `相當於幾座大安森林公園碳匯量` as  carbon_sink_equivalent_daan_forest_parks

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
    proxies = kwargs.get('proxies')
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    # Manually set
    rid = 'fcd166eb-4fb5-40db-962b-28899d7146fc'
    page_id = '687f5170-06e9-46be-80bc-fcae87bcaeba'
 
    # Extract
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)

    # Transform
    # Rename
    data = raw_data
    col_map = {
    "年度": "year",
    "查核家數": "audited_households",
    "節電量－萬度/年": "power_saving_ten_thousand_kwh_per_year",
    "減碳量－公噸": "carbon_reduction_metric_tons",
    "不合格家數": "non_compliant_households",
    "合格率": "compliance_rate",
    "複查合格率": "reinspection_compliance_rate",
    "相當於幾座大安森林公園碳匯量": "carbon_sink_daan_forest_parks"
}


    data = data.rename(columns=col_map)
    # Transfer year from ROC to AD
    data['year'] = data['year'].astype(int) + 1911
    data['compliance_rate'] = data['compliance_rate'].replace('%', '', regex=True)
    data['compliance_rate'] = data['compliance_rate'].astype(float)
    data['reinspection_compliance_rate'] = data['reinspection_compliance_rate'].replace('%', '', regex=True)
    data['audited_households'] = data['audited_households'].astype(int)
    data['carbon_sink_daan_forest_parks'] = data['carbon_sink_daan_forest_parks'].astype(int)
    data['power_saving_ten_thousand_kwh_per_year'] = data['power_saving_ten_thousand_kwh_per_year'].astype(int)
    data['non_compliant_households'] = data['non_compliant_households'].astype(int)
    # Time
    data['data_time'] = get_data_taipei_file_last_modified_time(page_id)
    data['data_time'] = convert_str_to_time_format(data['data_time'])
    data = data.drop(columns=['_id','_importdate'])
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

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='energy_saving_coaching_situation_tpe_gov')
dag.create_dag(etl_func=_transfer)
