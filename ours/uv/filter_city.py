import pandas as pd

df = pd.read_csv('uv_fake.csv')

df = df[df['City'] == '臺北市']

df.to_csv('uv_taipei_fake.csv', index=False)