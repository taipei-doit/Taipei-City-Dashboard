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
    
    # Debug: Print available columns and data sample
    print("Available columns:", list(data.columns))
    print("Data shape:", data.shape)
    print("First few rows of raw data:")
    print(data.head(10))
    print("\nUnique values in '統計期' column:")
    print(data['統計期'].unique())
    
    # Clean up year column
    data['year'] = data['統計期'].str.replace(r'[^\d]', '', regex=True)
    print("\nAfter year extraction:")
    print("Unique years:", data['year'].unique())
    
    data['year'] = data['year'].astype(int) + 1911
    print("After conversion to Western calendar:")
    print("Unique years:", data['year'].unique())
    
    # Rename basic columns
    data = data.rename(columns={
        '性別': 'gender'
    })
    
    # Process the wide format data into long format
    # Create records for each age group and metric type
    records = []
    
    # Define age groups - keep Chinese names as they appear in the database
    age_groups = [
        ("就業人口", "就業人口"),
        ("就業人口按年齡別/15至未滿20歲", "就業人口按年齡別/15-19歲"),
        ("就業人口按年齡別/20至未滿25歲", "就業人口按年齡別/20-24歲"),
        ("就業人口按年齡別/25至未滿30歲", "就業人口按年齡別/25-29歲"),
        ("就業人口按年齡別/30至未滿35歲", "就業人口按年齡別/30-34歲"),
        ("就業人口按年齡別/35至未滿40歲", "就業人口按年齡別/35-39歲"),
        ("就業人口按年齡別/40至未滿45歲", "就業人口按年齡別/40-44歲"),
        ("就業人口按年齡別/45至未滿50歲", "就業人口按年齡別/45-49歲"),
        ("就業人口按年齡別/50至未滿55歲", "就業人口按年齡別/50-54歲"),
        ("就業人口按年齡別/55至未滿60歲", "就業人口按年齡別/55-59歲"),
        ("就業人口按年齡別/60至未滿65歲", "就業人口按年齡別/60-64歲"),
        ("就業人口按年齡別/65歲以上", "就業人口按年齡別/65歲以上")
    ]
    
    for _, row in data.iterrows():
        year = row['year']
        gender = row['gender']
        
        for age_pattern, age_structure_name in age_groups:
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
                    'age_structure': age_structure_name,
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
