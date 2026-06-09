import pandas as pd
from sqlalchemy import create_engine

# Using the URI from .env
uri = "postgresql://tuic:M!2gAka41E1Q=%@citydashboard-prod.postgres.database.azure.com:5432/airflow?sslmode=require"
engine = create_engine(uri)

query = """
SELECT 
    table_schema, 
    table_name, 
    column_name, 
    data_type, 
    character_maximum_length
FROM 
    information_schema.columns 
WHERE 
    table_schema = 'public' 
    AND (table_name = 'tran_parking' OR table_name = 'tran_parking_history')
    AND character_maximum_length = 10;
"""

try:
    df = pd.read_sql(query, engine)
    print("Columns with length 10 found:")
    print(df)
except Exception as e:
    print(f"Error: {e}")

