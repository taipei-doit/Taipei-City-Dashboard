# -*- coding: utf-8 -*-
"""
交通部觀光署 ▶ 主題推薦 ▶ 穆斯林友善環境
一次擷取 臺北市 + 新北市 全部頁面
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ────────── Selenium 設定 ──────────
opt = Options()
opt.add_argument("--headless=new")          # 若要看瀏覽器畫面，把這行註解掉
opt.add_argument("--disable-gpu")
opt.add_argument("--no-sandbox")
opt.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=opt
)
driver.implicitly_wait(3)

URL = "https://www.taiwan.net.tw/m1.aspx?sNo=0020119&keyString=%5E10001%5E"
driver.get(URL)

# option value 來自 select ─ 「63=臺北市」「10001=新北市」
CITIES = [("臺北市", "63"),
          ("新北市", "10001")]

all_rows = []

for city_name, city_code in CITIES:
    print(f"\n切換到地區：{city_name}")

    # 1) 選擇城市
    sel = Select(WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "ddl_city_code"))
    ))
    sel.select_by_value(city_code)

    # 2) 點搜尋
    submit_btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ctl12_ibsubmit"))
    )
    driver.execute_script("arguments[0].click();", submit_btn)

    # 3) 等到表格地區正確
    WebDriverWait(driver, 20).until(
        lambda d: d.find_element(
            By.CSS_SELECTOR, "table tbody tr td:nth-child(2)"
        ).text.strip() == city_name
    )
    print("→ 資料載入完成")

    # 4) 逐頁擷取
    while True:
        # 4-1) 擷取本頁
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        for tr in driver.find_elements(By.CSS_SELECTOR, "table tbody tr"):
            tds = tr.find_elements(By.TAG_NAME, "td")
            if len(tds) >= 7:
                all_rows.append({
                    "單位名稱": tds[0].text.strip(),
                    "地區":     tds[1].text.strip(),
                    "認證別":   tds[2].text.strip(),
                    "淨下設備": tds[3].text.strip(),
                    "小淨設備": tds[4].text.strip(),
                    "祈禱室":   tds[5].text.strip(),
                    "認證單位": tds[6].text.strip()
                })

        # 4-2) 找下一頁：a.current 旁邊的兄弟節點
        try:
            next_a = driver.find_element(
                By.CSS_SELECTOR, "div.page-blk a.current + a")
        except Exception:
            break       # 沒有兄弟節點 = 最後一頁

        first_row_before = driver.find_element(
            By.CSS_SELECTOR, "table tbody tr").text
        driver.execute_script("arguments[0].click();", next_a)

        # 等第一列文字變化，確認翻頁成功
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(
                By.CSS_SELECTOR, "table tbody tr").text != first_row_before
        )

driver.quit()

# ────────── 匯出 CSV ──────────
df = pd.DataFrame(all_rows)
df.to_csv("muslim.csv",
          index=False, encoding="utf-8-sig")
print(f"\n已完成，共擷取 {len(df)} 筆資料，檔案：muslim_taipei_newtaipei_allpage.csv")
