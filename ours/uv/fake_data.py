import pandas as pd
import random
from datetime import datetime, timedelta

def generate_random_uv_data():
    # Read the original CSV file
    df = pd.read_csv('uv.csv')
    
    # Generate random UV index values between 0 and 11
    df['UVIndex'] = [random.randint(0, 11) for _ in range(len(df))]
    
    # Save the updated data
    df.to_csv('uv_fake.csv', index=False)
    print("UV data has been updated with random values between 0-11")

if __name__ == "__main__":
    generate_random_uv_data()
