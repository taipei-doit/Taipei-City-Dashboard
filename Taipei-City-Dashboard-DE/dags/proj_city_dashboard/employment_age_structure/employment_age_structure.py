from airflow import DAG
from operators.common_pipeline import CommonDag
from io import StringIO
import requests

def _transfer(**kwargs):
    import pandas as pd
    from sqlalchemy import create_engine

    from utils.load_stage import (
        save_dataframe_to_postgresql,
        update_lasttime_in_data_to_dataset_info,
    )
    from utils.get_time import get_tpe_now_time_str

    # Config
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    
    # Updated URL for new CSV data source
    url = 'https://tsis.dbas.gov.taipei/statis/webMain.aspx?sys=220&ymf=6700&kind=21&type=0&funid=a05005301&cycle=4&outmode=12&compmode=0&outkind=3&deflst=2&nzo=1'
    ENCODING = 'utf-8-sig'
    raw_data = pd.read_csv(url, encoding=ENCODING)

    data = raw_data.copy()
    
    # Debug: Print available columns
    print("Available columns:", list(data.columns))
    
    # Clean up year column
    data['year'] = data['統計期'].str.replace(r'[^\d]', '', regex=True)
    data['year'] = data['year'].astype(int) + 1911
    
    # Rename basic columns
    data = data.rename(columns={
        '性別': 'gender'
    })
    
    # Process the wide format data into long format
    # Create records for each age group and metric type
    records = []
    
    # Define age groups and their corresponding column patterns
    age_groups = [
        ("就業人口", "employment_total"),
        ("就業人口按年齡別/15至未滿20歲", "age_15_20"),
        ("就業人口按年齡別/20至未滿25歲", "age_20_25"),
        ("就業人口按年齡別/25至未滿30歲", "age_25_30"),
        ("就業人口按年齡別/30至未滿35歲", "age_30_35"),
        ("就業人口按年齡別/35至未滿40歲", "age_35_40"),
        ("就業人口按年齡別/40至未滿45歲", "age_40_45"),
        ("就業人口按年齡別/45至未滿50歲", "age_45_50"),
        ("就業人口按年齡別/50至未滿55歲", "age_50_55"),
        ("就業人口按年齡別/55至未滿60歲", "age_55_60"),
        ("就業人口按年齡別/60至未滿65歲", "age_60_65"),
        ("就業人口按年齡別/65歲以上", "age_65_plus")
    ]
    
    for _, row in data.iterrows():
        year = row['year']
        gender = row['gender']
        
        for age_pattern, age_code in age_groups:
            # Find columns for this age group
            actual_col = None
            percentage_col = None
            
            for col in data.columns:
                if age_pattern in col and "實數[千人]" in col:
                    actual_col = col
                elif age_pattern in col and "百分比[%]" in col:
                    percentage_col = col
            
            if actual_col and percentage_col:
                actual_value = row[actual_col]
                percentage_value = row[percentage_col]
                
                # Handle missing or invalid values - we'll include all records for percentage tracking
                # Even if actual_value is 0 or missing, we still want the percentage data
                    
                records.append({
                    'year': year,
                    'gender': gender,
                    'age_structure': age_code,
                    'percentage': percentage_value if pd.notna(percentage_value) and percentage_value != '-' else None
                })
    
    # Create new dataframe from records
    if records:
        data = pd.DataFrame(records)
        
        # Convert data types to match database schema
        data['year'] = data['year'].astype(int)
        data['percentage'] = pd.to_numeric(data['percentage'], errors='coerce')
        
        # Add data_time column
        data["data_time"] = get_tpe_now_time_str(is_with_tz=True)
        
        print(f"Processed {len(data)} records")
        print("Sample data:")
        print(data.head())
        print("Data types:")
        print(data.dtypes)
        
    else:
        raise ValueError("No valid records were processed from the CSV data")
    
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, data["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="employment_age_structure")
dag.create_dag(etl_func=_transfer)
