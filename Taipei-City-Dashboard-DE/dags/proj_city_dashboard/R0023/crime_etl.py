#crime
#R0023, R0024, R0025, R0026, R0027
def crime_etl(url, encoding, from_crs, geometry_type, **kwargs):
    import re

    import pandas as pd
    from sqlalchemy import create_engine
    from utils.load_stage import (
        save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
    )
    from utils.transform_address import (
        clean_data, get_addr_xy_parallel, main_process, save_data
    )
    from utils.transform_geometry import add_point_wkbgeometry_column_to_df
    from utils.transform_time import convert_str_to_time_format


    def _period_hour_to_time(period_hour, split_str='~'):
        '00~02 -> 01:00:00'
        # print('phour:',period_hour.split(split_str))
        if '~' in period_hour:
            start, end = period_hour.split(split_str)
        elif '-' in period_hour:
            start, end = period_hour.split('-')
        elif '月' in period_hour or '日' in period_hour:
            pattern = re.compile(r'\d{2}')
            start, end = pattern.findall(period_hour)
        hour = (int(start) + int(end)) / 2
        time = str(int(hour)).zfill(2) + ':00:00'
        return time


    # Config
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')

    # Extract
    raw_data = pd.read_csv(url, encoding=encoding)

    # Transform
    data = raw_data.copy()
    # rename
    data = data.rename(columns={
        '案類': 'type',
        # '\ufeff編號': 'case_id',
        '編號': 'case_id',
        '發生地點': 'location',
        '發生日期': 'date',
        '發生時段': 'time',
        'geometry': 'wkb_geometry'
    })
    # omit empty rows
    data = data.dropna(subset=['case_id'])
    # clean str columns
    data['case_id'] = data['case_id'].astype(str)
    data['case_id'] = data['case_id'].str.replace('.0', '', regex=False)
    data['date'] = data['date'].astype(str)
    data['date'] = data['date'].str.replace('.0', '', regex=False)
    # standardize time
    data['date'] = convert_str_to_time_format(
        data['date'],
        from_format='%TY%m%d',
        output_level='date',
        output_type='str',
        errors='coerce'
    )
    data['time'] = data['time'].apply(lambda x: x if isinstance(x, str) else '22~24')
    data['time'] = data['time'].map(_period_hour_to_time)
    data['begin_when'] = data['date'] + ' ' + data['time']
    data['begin_when'] = convert_str_to_time_format(data['begin_when'], errors='coerce')
    data['epoch_time'] = data['begin_when'].map(lambda x: pd.NaT if x is pd.NaT else x.timestamp())

    # clean addr
    addr = data['location']
    addr_cleaned = clean_data(addr)
    standard_addr_list = main_process(addr_cleaned)
    result, output = save_data(addr, addr_cleaned, standard_addr_list)
    data['address'] = output
    # standardize geometry
    x, y = get_addr_xy_parallel(output)
    gdata = add_point_wkbgeometry_column_to_df(data, x, y, from_crs=from_crs)
    # select columns
    ready_data = gdata[[
        'case_id', 'type',
        'date', 'time', 'begin_when', 'epoch_time',
        'location', 'address', 'wkb_geometry'
    ]]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine, gdata=ready_data, load_behavior=load_behavior,
        default_table=default_table, geometry_type=geometry_type
    )
    lasttime_in_data = data['begin_when'].max()
    update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)
