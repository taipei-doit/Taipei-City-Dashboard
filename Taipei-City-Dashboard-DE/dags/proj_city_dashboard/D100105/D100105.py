from airflow import DAG
from operators.common_pipeline import CommonDag
from sqlalchemy import create_engine
import pandas as pd

def _extract_db_info(default_table, engine):
    # read existing data
    existing_data = pd.read_sql(f"SELECT * FROM {default_table}", engine)

    # Filter columns
    keep_col = ['name', 'addr', 'lat', 'lng']
    existing_data = existing_data[keep_col]
    return existing_data

def _concat_hospital_clinic_info(clinic_table, hospital_table, **kwargs):
    # Config
    raw_data_db_uri = kwargs.get('raw_data_db_uri')

    # Get existing hospital and clinic data
    engine = create_engine(raw_data_db_uri)
    clinic_data = _extract_db_info('heal_clinic', engine)
    hospital_data = _extract_db_info('heal_hospital', engine)

    # Concat
    existing_data = pd.concat([clinic_data, hospital_data], axis=0)
    return existing_data


def D100105(**kwargs):
    '''
    Information and locations of Obstetrics and Gynecology Medical Institution from data.taipei.

    Explanation:
    -------------
    unmatched_list: There are 10 hospitals in the raw data that cannot be found in the existing 
        hospital and clinic list, therefore the list was created to record the situation.
        Therefore, we manually add the address for these hospitals.
    '''
    import pandas as pd
    from utils.transform_time import convert_str_to_time_format
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_address import clean_data, main_process, save_data, get_addr_xy_parallel
    from utils.extract_stage import get_data_taipei_file_last_modified_time, get_data_taipei_api
    from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    from sqlalchemy import create_engine

    # Config
    # Retrieve all kwargs automatically generated upon DAG initialization
    raw_data_db_uri = kwargs.get('raw_data_db_uri')
    data_folder = kwargs.get('data_folder')
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')
    # Retrieve some essential args from `job_config.json`.
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    clinic_table = 'heal_clinic'
    hospital_table = 'heal_hospital'
    # Manually set
    rid = 'ba860191-ad03-49a3-8df4-29e0a01f3026'
    page_id = '83dc0502-245a-4d77-99f4-786127cedea2'
    from_crs = 4326

    # Extract
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)

    # Transform
    # Filter columns
    data = raw_data.copy()
    keep_col = ['機構名稱']
    data = data[keep_col]
    data = data.rename(columns={'機構名稱': 'name'})
    # Geometry from existing data
    replace_dict = {'\n': '', ' ': '', '-': '─', '－': '─', '台':'臺'}
    data['name'] = data['name'].replace(replace_dict, regex=True)
    existing_data = _concat_hospital_clinic_info(clinic_table, hospital_table, **kwargs)
    existing_data['name'] = existing_data['name'].replace(replace_dict, regex=True)
    data = data.merge(existing_data, how='left', left_on='name', right_on='name')
    data = data.rename(columns={'addr': 'address'})
    unmatch_list = data[data['lng'].isnull()]
    print(f"Unmatched {len(unmatch_list)} hospitals: {unmatch_list['name'].to_list()}")
    # Match unmatched_list
    manual_address = {
    '聖心婦家醫診所': '臺北市大同區保安街1之1號',
    '繼承婦產科診所': '臺北市中山區松江路276號5樓',
    '羅浮婦女診所': '臺北市中山區長安東路二段90號12樓',
    '詩宓診所': '臺北市中山區民生東路二段161號3樓',
    '瑞麗嘉健康美學慶中診所': '臺北市松山區南京東路三段259號5F',
    '楊鵬生婦產科診所': '臺北市大安區信義路二段72號2樓',
    '禾馨宜蘊婦產科診所': '臺北市大安區信義路三段149號14樓',
    '禾馨大安婦幼診所': '臺北市大安區新生南路三段2號',
    '國立臺灣大學醫學院附設醫院癌醫中心分院': '臺北市大安區基隆路三段155巷57號',
    '鄢源貴婦產科診所': '臺北市大安區信義路四段199巷2號5樓之一',
    '劉教授婦產科診所': '臺北市信義區忠孝東路五段236巷32號1樓',
    '臺北市立萬芳醫院─委託臺北醫學大學辦理': '臺北市文山區興隆路三段111號',
    '愛文婦產科診所': '臺北市文山區木柵路四段143號1樓'
    }
    data['address'] = data['address'].fillna(data['name'].map(manual_address))
    # clean addr
    addr = data['address']
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    data['address'] = output
    # extract town
    data['town'] = data['address'].apply(lambda x: x[3:6])
    # Time
    data['data_time'] = get_data_taipei_file_last_modified_time(page_id)
    data['data_time'] = convert_str_to_time_format(data['data_time'])
    # Replace missing lng, lat
    unmatch_list = data[data['lng'].isnull()]
    unmatch_list['lng'], unmatch_list['lat'] = get_addr_xy_parallel(
        unmatch_list['address'], sleep_time=0.5
    )
    for index, row in unmatch_list.iterrows():
        data.loc[data['name'] == row['name'], 'lng'] = row['lng']
        data.loc[data['name'] == row['name'], 'lat'] = row['lat']
    # Check left unmatched hospital
    unmatch_list = data[data['lng'].isnull()]['name'].values.tolist()
    print(f'Still unmatched {len(unmatch_list)} hospitals: {unmatch_list}')
    gdata = add_point_wkbgeometry_column_to_df(
        data, x=data['lng'], y=data['lat'], from_crs=from_crs
    )
    # Reshape
    ready_data = gdata.drop(columns=['geometry'])

    # Load
    # Load data to DB
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine, gdata=ready_data, load_behavior=load_behavior,
        default_table=default_table, history_table=history_table,
        geometry_type='Point'
    )
    # Update lasttime_in_data
    lasttime_in_data = ready_data['data_time'].max()
    engine = create_engine(ready_data_db_uri)
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data
    )

dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='D100105')
dag.create_dag(etl_func=D100105)
