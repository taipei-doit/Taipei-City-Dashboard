import pandas as pd
import requests
import time
from tqdm import tqdm  # 新增進度條套件

# 設定你的 Google API 金鑰
API_KEY = 'AIzaSyCGKB73qpabPw2WUHefJtEqlfmZWv2T0HY'
GEOCODE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'

# 讀取 CSV 檔案（請確認檔案路徑正確）
df = pd.read_csv(r'C:\Users\how08\Desktop\黑克松\blood_donation_info_total_20250531.csv')

# 檢查必須的欄位
required_fields = ['地點']
for field in required_fields:
    if field not in df.columns:
        raise ValueError(f"缺少必要欄位: {field}")

# 建立 Latitude 和 Longitude 欄位
df['Latitude'] = None
df['Longitude'] = None

# 使用 tqdm 包裝迴圈，顯示進度條
for index, row in tqdm(df.iterrows(), total=len(df), desc="查詢地址"):
    full_address = f"{row['地點']}"
    params = {
        'address': full_address,
        'key': API_KEY
    }

    response = requests.get(GEOCODE_URL, params=params)
    data = response.json()

    if data['status'] == 'OK':
        location = data['results'][0]['geometry']['location']
        df.at[index, 'Latitude'] = location['lat']
        df.at[index, 'Longitude'] = location['lng']
    else:
        print(f"查詢失敗：{full_address}，錯誤代碼：{data['status']}")

    time.sleep(0.2)  # 防止超過 API 配額限制

# 儲存含經緯度的結果
df.to_csv('output_with_coordinates.csv', index=False)
print("✅ 查詢完成，已儲存為 blood.csv")
