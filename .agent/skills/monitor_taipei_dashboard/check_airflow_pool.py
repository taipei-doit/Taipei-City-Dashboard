#!/usr/bin/env python3
"""
Airflow Pool Monitor Script

此腳本用來定期檢查 Airflow 的 default_pool，
確認 Queued Slots 或 Scheduled Slots 數量是否超過設定的警示閾值（代表任務卡住），
如果異常則透過 SMTP 發送警告信件。

支援讀取 .env 檔案以載入環境變數（如 SMTP_USER, SMTP_PASSWORD 等）。
"""

import os
import argparse
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_env(filepath):
    """
    簡單讀取 .env 檔案，並將設定載入至 os.environ 中
    （不依賴外部套件 python-dotenv，維持 standalone）
    """
    if not filepath or not os.path.exists(filepath):
        print(f"環境變數檔案 {filepath} 不存在，將忽略並使用系統預設環境變數。")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip("'").strip('"')
                # 以檔案內讀取的值為主，若要被系統環境變數覆蓋可改用 setdefault
                os.environ[k] = v

def get_config():
    """取得檢查與發信所需的各項設定"""
    return {
        # Airflow API 設定
        "AIRFLOW_API_URL": os.getenv("AIRFLOW_API_URL", "https://test-citydashboard.taipei/airflow-prod/api/v1/pools/default_pool"),
        "AIRFLOW_USER": os.getenv("AIRFLOW_USER", "tuic"),
        "AIRFLOW_PASS": os.getenv("AIRFLOW_PASS", "1Qaz2wsx3edc"),
        
        # 警告閾值設定
        "THRESHOLD_QUEUED": int(os.getenv("THRESHOLD_QUEUED", 30)),
        "THRESHOLD_SCHEDULED": int(os.getenv("THRESHOLD_SCHEDULED", 30)),
        
        # Email (SMTP) 設定：對應您的 .env 中的變數名稱
        "SMTP_HOST": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "SMTP_PORT": int(os.getenv("SMTP_PORT", 587)),
        "SMTP_USER": os.getenv("SMTP_USER", ""),
        "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD", ""),
        "SMTP_MAIL_FROM": os.getenv("SMTP_MAIL_FROM", os.getenv("SMTP_USER", "")),
        # 若未指定收件者 (SMTP_TO)，預設使用群組聯絡人名單
        "SMTP_TO": os.getenv("SMTP_TO", "webber.ys.lin@foxconn.com,perry.ph.wu@foxconn.com,benji.tsai@foxconn.com,j61723@gov.taipei,wp6223@gov.taipei"),
    }

def send_email_alert(title: str, message: str, config: dict):
    """透過 SMTP 發送警告信件"""
    print(f"[{title}]\n{message}")

    smtp_user = config["SMTP_USER"]
    smtp_pass = config["SMTP_PASSWORD"]
    smtp_from = config["SMTP_MAIL_FROM"]
    smtp_to = config["SMTP_TO"]
    
    if not smtp_user or not smtp_pass:
        print(">> 未設定 SMTP 帳號密碼 (SMTP_USER / SMTP_PASSWORD)，僅將輸出印至一般日誌。")
        return

    msg = MIMEMultipart()
    msg['From'] = smtp_from
    msg['To'] = smtp_to
    msg['Subject'] = title

    msg.attach(MIMEText(message, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(config["SMTP_HOST"], config["SMTP_PORT"])
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        print(">> Email 警報已發送成功。")
    except Exception as e:
        print(f">>> 發送 Email 失敗: {e}")

def check_airflow_pool(config: dict):
    """檢查 Airflow Pool，若異常則觸發發信"""
    api_url = config["AIRFLOW_API_URL"]
    print(f"正在檢查 Airflow Pool 狀態: {api_url} ...")
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        auth = (config["AIRFLOW_USER"], config["AIRFLOW_PASS"]) if config["AIRFLOW_USER"] and config["AIRFLOW_PASS"] else None
        
        response = requests.get(api_url, headers=headers, auth=auth, timeout=15)
        
        if response.status_code in (401, 403):
            send_email_alert(
                "Airflow Pool 監控異常",
                f"無法連線 API 取得狀態，連線回傳 {response.status_code}。\n可能憑證 (AIRFLOW_USER / AIRFLOW_PASS) 設定錯誤。",
                config
            )
            return
            
        response.raise_for_status()
        data = response.json()
        
        pool_name = data.get("name", "Unknown")
        queued_slots = data.get("queued_slots", 0)
        scheduled_slots = data.get("scheduled_slots", 0)
        running_slots = data.get("running_slots", 0)

        alarms = []
        th_q = config["THRESHOLD_QUEUED"]
        th_s = config["THRESHOLD_SCHEDULED"]
        if queued_slots >= th_q:
            alarms.append(f"- Queued Slots ({queued_slots}) 已達到或超過警示門檻 ({th_q})")
        if scheduled_slots >= th_s:
            alarms.append(f"- Scheduled Slots ({scheduled_slots}) 已達到或超過警示門檻 ({th_s})")

        if alarms:
            msg = "偵測到以下異常，可能有部分 DAG 正在卡住：\n" + "\n".join(alarms) + f"\n\n目前 Running Slots: {running_slots}"
            send_email_alert(f"Airflow({pool_name}) - 任務塞車警報", msg, config)
        else:
            print(f"[{pool_name}] 狀態正常 -> Queued: {queued_slots}, Scheduled: {scheduled_slots}, Running: {running_slots}")

    except Exception as e:
         send_email_alert("Airflow Pool 監控異常", f"連線或解析 API 時發生例外錯誤：\n{str(e)}", config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Airflow Pool Monitor")
    parser.add_argument("--env-file", type=str, help="指定 .env 檔案路徑", default="")
    args = parser.parse_args()
    
    if args.env_file:
        load_env(args.env_file)
        
    conf = get_config()
    check_airflow_pool(conf)
