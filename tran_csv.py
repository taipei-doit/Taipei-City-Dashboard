import pandas as pd
import requests
import time
from tqdm import tqdm
import re

# 設定 Google API 金鑰
API_KEY = 'AIzaSyCGKB73qpabPw2WUHefJtEqlfmZWv2T0HY'
GEOCODE_URL = 'https://maps.googleapis.com/maps/api/geocode/json'

# 清理地址函式（可依需要調整）
def clean_address(addr):
    # 例如：去除括號內文字、替換特殊符號
    addr = addr.replace('+', '與')
    addr = re.sub(r'\(.*?\)', '', addr)
    return addr.strip()

# 讀取資料
df = pd.read_csv(r'C:\Users\how08\Desktop\黑克松\blood.csv', encoding='utf-8')

# 檢查必要欄位
required_fields = ['地點']
for field in required_fields:
    if field not in df.columns:
        raise ValueError(f"缺少必要欄位: {field}")

# 建立新欄位
df['Latitude'] = None
df['Longitude'] = None
df['行政區'] = None

# 逐筆查詢地址經緯度及行政區
for index, row in tqdm(df.iterrows(), total=len(df), desc="查詢地址與行政區"):
    raw_address = row['地點']
    full_address = clean_address(raw_address)

    params = {
        'address': full_address,
        'key': API_KEY,
        'language': 'zh-TW'
    }

    try:
        response = requests.get(GEOCODE_URL, params=params, timeout=5)
        data = response.json()

        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            lat = location['lat']
            lng = location['lng']
            df.at[index, 'Latitude'] = lat
            df.at[index, 'Longitude'] = lng

            # 反向查詢行政區
            reverse_params = {
                'latlng': f"{lat},{lng}",
                'key': API_KEY,
                'language': 'zh-TW'
            }
            rev_response = requests.get(GEOCODE_URL, params=reverse_params, timeout=5)
            rev_data = rev_response.json()

            if rev_data['status'] == 'OK':
                district = None
                for result in rev_data['results']:
                    for comp in result['address_components']:
                        if 'administrative_area_level_2' in comp['types']:
                            district = comp['long_name']
                            break
                    if district:
                        break
                df.at[index, '行政區'] = district
            else:
                print(f"⚠️ 反查行政區失敗：({lat}, {lng})，錯誤代碼：{rev_data['status']}")

        else:
            print(f"❌ 地址查詢失敗：{full_address}，錯誤代碼：{data['status']}")

    except requests.exceptions.RequestException as e:
        print(f"❌ 請求異常：{full_address}，錯誤訊息：{e}")

    time.sleep(0.3)  # 防止 API 過度請求

# 儲存結果為 UTF-8 with BOM（Excel 相容）
df.to_csv('oldclub_with_district.csv', index=False, encoding='utf-8-sig')
print("✅ 經緯度與行政區查詢完成，已儲存為 oldclub_with_district.csv")
