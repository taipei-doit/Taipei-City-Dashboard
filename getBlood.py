import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

def get_blood_donation_info(url="https://www.blood.org.tw/xcevent", county=None, district=None, date_start=None, date_end=None, max_pages=None):
    """
    從台灣血液基金會網站抓取捐血活動資訊，支援翻頁功能
    
    參數:
    url (str): 血液基金會的URL
    county (str): 縣市名稱，例如 "臺北市", "新北市" 等
    district (str): 地區名稱，例如 "中正區", "信義區" 等
    date_start (str): 開始日期，格式為 "YYYY/MM/DD"
    date_end (str): 結束日期，格式為 "YYYY/MM/DD"
    max_pages (int): 最大爬取頁數，None表示爬取所有頁面
    """
    driver = None
    try:
        # 設置Chrome選項
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 無頭模式，不顯示瀏覽器
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # 初始化WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # 訪問網頁
        driver.get(url)
        print("網頁已載入")
        
        # 等待頁面載入完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "rwdTable"))
        )
        
        # 填寫搜尋條件
        if date_start and date_end:
            try:
                # 填寫開始日期
                start_date_input = driver.find_element(By.NAME, "start_date")
                start_date_input.clear()
                start_date_input.send_keys(date_start)
                print(f"已填入開始日期: {date_start}")
                
                # 填寫結束日期
                end_date_input = driver.find_element(By.NAME, "end_date")
                end_date_input.clear()
                end_date_input.send_keys(date_end)
                print(f"已填入結束日期: {date_end}")
            except Exception as e:
                print(f"填寫日期時發生錯誤: {e}")
        
        if county:
            try:
                # 檢查縣市選擇器的ID
                # 使用不同的選擇器嘗試找到縣市下拉選單
                county_select_element = None
                for selector in ["#bloodCounty", "select[name='county']", "select"]:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            print(f"找到可能的縣市選擇器: {selector}")
                            options_text = [option.text for option in element.find_elements(By.TAG_NAME, "option")]
                            if "臺北市" in options_text or "台北市" in options_text or "新北市" in options_text:
                                county_select_element = element
                                print(f"確認找到縣市選擇器: {selector}")
                                break
                        if county_select_element:
                            break
                    except:
                        continue
                
                if county_select_element:
                    # 使用Select對象來選擇縣市
                    county_select = Select(county_select_element)
                    
                    # 獲取所有選項文本
                    options = [option.text for option in county_select.options]
                    print(f"可用的縣市選項: {options}")
                    
                    # 選擇縣市
                    if county in options:
                        county_select.select_by_visible_text(county)
                        print(f"已選擇縣市: {county}")
                    else:
                        print(f"找不到縣市選項: {county}")
                    
                    # 等待地區選單載入
                    time.sleep(2)
                    
                    if district:
                        try:
                            # 嘗試不同的選擇器來找到地區下拉選單
                            district_select_element = None
                            for selector in ["#bloodDistrict", "select[name='area']", "select"]:
                                try:
                                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                    for element in elements:
                                        if element != county_select_element:  # 確保不是縣市選擇器
                                            options_text = [option.text for option in element.find_elements(By.TAG_NAME, "option")]
                                            print(f"可能的地區選項: {options_text}")
                                            if len(options_text) > 1:  # 至少有兩個選項（包括預設選項）
                                                district_select_element = element
                                                print(f"確認找到地區選擇器: {selector}")
                                                break
                                    if district_select_element:
                                        break
                                except:
                                    continue
                            
                            if district_select_element:
                                # 使用Select對象選擇地區
                                district_select = Select(district_select_element)
                                options = [option.text for option in district_select.options]
                                print(f"可用的地區選項: {options}")
                                
                                if district in options:
                                    district_select.select_by_visible_text(district)
                                    print(f"已選擇地區: {district}")
                                else:
                                    print(f"找不到地區選項: {district}")
                            else:
                                print("找不到地區選擇器")
                        except Exception as e:
                            print(f"選擇地區時出錯: {e}")
                else:
                    print("找不到縣市選擇器")
            except Exception as e:
                print(f"選擇縣市時出錯: {e}")
        
        # 點擊搜尋按鈕
        try:
            search_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
            if search_buttons:
                for button in search_buttons:
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        print("已點擊搜尋按鈕")
                        break
            else:
                print("找不到搜尋按鈕")
        except Exception as e:
            print(f"點擊搜尋按鈕時出錯: {e}")
        
        # 等待搜尋結果載入
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "rwdTable"))
            )
            print("搜尋結果已載入")
        except TimeoutException:
            print("等待搜尋結果超時，使用當前頁面")
        
        # 用於保存所有頁面的數據
        all_donation_data = []
        current_page = 1
        
        # 翻頁並收集數據
        while True:
            print(f"正在處理第 {current_page} 頁...")
            
            # 獲取當前頁面源碼並使用BeautifulSoup解析
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 找到表格
            table = soup.find('table', class_='rwdTable')
            if not table:
                print("找不到捐血活動表格，請檢查網站結構是否有變更")
                break
            
            # 解析表格數據
            rows = table.find_all('tr')
            
            # 檢查是否有數據行（跳過標題行）
            if len(rows) <= 1:
                print("本頁沒有捐血活動數據")
                break
            
            # 解析表格數據（跳過標題行）
            page_data = []
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    # 解析數據
                    operation_time = cols[0].text.strip()
                    date = cols[1].text.strip()
                    
                    # 獲取捐血點/主辦單位
                    title_col = cols[2]
                    location_type = ""
                    # 檢查該欄位的class來判斷類型(固定點、巡迴車、活動)
                    if 'station' in title_col.get('class', []):
                        location_type = "固定點"
                    elif 'mobile' in title_col.get('class', []):
                        location_type = "巡迴車"
                    elif 'drive' in title_col.get('class', []):
                        location_type = "活動"
                    
                    # 獲取捐血點名稱
                    title_link = title_col.find('a')
                    title = title_link.text.strip() if title_link else cols[2].text.strip()
                    event_id = ""
                    if title_link and 'href' in title_link.attrs:
                        # 從URL中提取活動ID
                        href = title_link['href']
                        if 'sid=' in href:
                            event_id = href.split('sid=')[1]
                    
                    location = cols[3].text.strip()
                    waiting_num = cols[4].text.strip()
                    
                    # 存儲數據
                    page_data.append({
                        '作業時間': operation_time,
                        '日期': date,
                        '類型': location_type,
                        '捐血點/主辦單位': title,
                        '地點': location,
                        '等候人數': waiting_num,
                        '活動ID': event_id,
                        '頁碼': current_page,
                        '縣市': county if county else "全部"
                    })
            
            # 添加當前頁面數據到總數據中
            all_donation_data.extend(page_data)
            print(f"第 {current_page} 頁抓取到 {len(page_data)} 筆數據")
            
            # 檢查是否達到最大頁數限制
            if max_pages and current_page >= max_pages:
                print(f"已達到設定的最大頁數 {max_pages}，停止抓取")
                break
            
            # 尋找下一頁按鈕
            try:
                # 嘗試多種選擇器來找到下一頁按鈕
                next_page_link = None
                for selector in ["a.next[title='下一頁']", "a.next", "a:contains('下一頁')", "a[onclick*='pagingHelper.getList']"]:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if "下一頁" in element.get_attribute("title") or "下一頁" in element.text:
                                next_page_link = element
                                print(f"找到下一頁按鈕: {selector}")
                                break
                        if next_page_link:
                            break
                    except:
                        continue
                
                if not next_page_link:
                    print("找不到下一頁按鈕，可能已到達最後一頁")
                    break
                
                # 檢查下一頁按鈕是否可點擊
                if "disabled" in next_page_link.get_attribute("class") or not next_page_link.is_displayed():
                    print("下一頁按鈕被禁用或不可見，已到達最後一頁")
                    break
                
                # 使用JavaScript點擊下一頁按鈕（更可靠）
                driver.execute_script("arguments[0].click();", next_page_link)
                print("已點擊下一頁按鈕")
                
                # 等待數據加載
                time.sleep(3)  # 稍微增加等待時間，確保頁面加載完成
                
                current_page += 1
            except NoSuchElementException:
                print("找不到下一頁按鈕，可能已到達最後一頁")
                break
            except TimeoutException:
                print("等待下一頁超時，停止抓取")
                break
            except Exception as e:
                print(f"翻頁時發生錯誤: {e}")
                break
        
        # 關閉瀏覽器
        driver.quit()
        
        # 檢查是否有抓取到數據
        if not all_donation_data:
            print("沒有抓取到任何捐血活動資訊")
            return None
        
        # 轉換為Pandas DataFrame
        df = pd.DataFrame(all_donation_data)
        print(f"總共抓取到 {len(df)} 筆捐血活動資訊")
        return df
    
    except Exception as e:
        print(f"發生錯誤: {e}")
        if driver:
            driver.quit()
        return None

def save_to_csv(df, filename=None):
    """
    將抓取的數據保存為CSV文件
    """
    if df is None or df.empty:
        print("沒有數據可以保存")
        return None
    
    # 如果沒有指定文件名，則使用當前日期作為文件名
    if filename is None:
        today = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"blood_donation_info_{today}.csv"
    
    # 確保目錄存在
    os.makedirs("data", exist_ok=True)
    filepath = os.path.join("data", filename)
    
    # 保存為CSV
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"捐血活動資訊已保存至 {filepath}")
    return filepath

def parse_args():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description='抓取台灣血液基金會捐血活動資訊')
    parser.add_argument('--county', type=str, help='縣市名稱，例如: 臺北市, 新北市')
    parser.add_argument('--district', type=str, help='地區名稱，例如: 中正區, 信義區')
    parser.add_argument('--start_date', type=str, help='開始日期，格式: YYYY/MM/DD')
    parser.add_argument('--end_date', type=str, help='結束日期，格式: YYYY/MM/DD')
    parser.add_argument('--max_pages', type=int, help='最大爬取頁數，預設為所有頁面')
    parser.add_argument('--output', type=str, help='輸出文件名，預設使用當前日期')
    return parser.parse_args()

def scrape_city(city_name, max_pages=None):
    """抓取指定縣市的捐血活動資訊"""
    print(f"\n=== 開始抓取 {city_name} 的捐血活動資訊 ===\n")
    
    df = get_blood_donation_info(
        county=city_name,
        district=None,
        date_start=None,
        date_end=None,
        max_pages=max_pages
    )
    
    if df is not None and not df.empty:
        print(f"成功抓取 {city_name} 的 {len(df)} 筆捐血活動資訊")
        print("\n資料預覽:")
        print(df.head())
        
        # 保存城市特定的資料
        today = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"blood_donation_info_{city_name}_{today}.csv"
        filepath = save_to_csv(df, filename)
        
        return df
    else:
        print(f"未能抓取到 {city_name} 的捐血活動資訊")
        return None

def main():
    args = parse_args()
    
    # 檢查是否使用命令行參數
    if args.county or args.district or args.start_date or args.end_date or args.max_pages or args.output:
        # 使用命令行參數執行
        county = args.county
        district = args.district
        date_start = args.start_date
        date_end = args.end_date
        max_pages = args.max_pages
        output_file = args.output
        
        print("爬蟲參數設置:")
        print(f"- 縣市: {county or '全部'}")
        print(f"- 地區: {district or '全部'}")
        print(f"- 開始日期: {date_start or '不限'}")
        print(f"- 結束日期: {date_end or '不限'}")
        print(f"- 最大頁數: {max_pages or '所有頁面'}")
        
        # 抓取資料
        df = get_blood_donation_info(
            county=county,
            district=district,
            date_start=date_start,
            date_end=date_end,
            max_pages=max_pages
        )
        
        if df is not None and not df.empty:
            print(f"成功抓取 {len(df)} 筆捐血活動資訊")
            print("\n資料預覽:")
            print(df.head())
            filepath = save_to_csv(df, output_file)
            print(f"完整結果已保存至: {filepath}")
        else:
            print("未能抓取到捐血活動資訊")
    else:
        # 自動模式: 依次抓取新北市和台北市
        print("=== 自動模式: 依次抓取新北市和台北市的捐血活動資訊 ===")
        
        # 創建空DataFrame來保存所有數據
        all_data = pd.DataFrame()
        
        # 依次抓取新北市和台北市
        cities = ["新北市", "臺北市"]
        for city in cities:
            city_df = scrape_city(city)
            if city_df is not None and not city_df.empty:
                all_data = pd.concat([all_data, city_df], ignore_index=True)
        
        # 保存所有數據到一個總檔案
        if not all_data.empty:
            today = datetime.datetime.now().strftime("%Y%m%d")
            total_filename = f"blood_donation_info_total_{today}.csv"
            total_filepath = save_to_csv(all_data, total_filename)
            print(f"\n=== 全部抓取完成 ===")
            print(f"總共抓取到 {len(all_data)} 筆捐血活動資訊")
            print(f"完整結果已保存至: {total_filepath}")
        else:
            print("\n=== 未能抓取到任何捐血活動資訊 ===")

if __name__ == "__main__":
    main()
