import pandas as pd
import requests
import time
from tqdm import tqdm

# 設定你的 Google API 金鑰
API_KEY = 'AIzaSyCGKB73qpabPw2WUHefJtEqlfmZWv2T0HY'
GEOCODE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'

# 讀取 CSV 檔案（請確認檔案路徑正確）
df = pd.read_csv(r'C:\Users\how08\Desktop\黑克松\雙北銀髮俱樂部_填補.csv', encoding='utf-8')

# 檢查必須的欄位
required_fields = ['county', 'town', 'address']
for field in required_fields:
    if field not in df.columns:
        raise ValueError(f"缺少必要欄位: {field}")

# 建立新的經緯度欄位
df['Latitude'] = None
df['Longitude'] = None

# 使用 tqdm 包裝迴圈，顯示進度條
for index, row in tqdm(df.iterrows(), total=len(df), desc="查詢地址"):
    full_address = f"{row['county']}{row['town']}{row['address']}".strip()
    params = {
        'address': full_address,
        'key': API_KEY
    }

    try:
        response = requests.get(GEOCODE_URL, params=params, timeout=5)
        data = response.json()

        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            df.at[index, 'Latitude'] = location['lat']
            df.at[index, 'Longitude'] = location['lng']
        else:
            print(f"❌ 查詢失敗：{full_address}，錯誤代碼：{data['status']}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 請求異常：{full_address}，錯誤訊息：{e}")

    time.sleep(0.2)  # 限流防超額

# 儲存含經緯度的結果，指定 UTF-8 編碼（Excel 相容）
df.to_csv('oldclub.csv', index=False, encoding='utf-8-sig')
print("✅ 查詢完成，已儲存為 oldclub.csv（含 BOM 編碼，支援 Excel 中文）")
