import requests, urllib3
urllib3.disable_warnings()

urls = [
    "https://tsis.dbas.gov.taipei/statis/webMain.aspx?sys=220&ymf=8700&kind=21&type=0&funid=a05007301&cycle=4&outmode=12&compmode=0&outkind=1&deflst=2&nzo=1"
]
headers = {"User-Agent": "Mozilla/5.0"}

for i, url in enumerate(urls):
    resp = requests.get(url, headers=headers, timeout=30, verify=False)
    print(f"=== URL {i+1} ===")
    print("Status:", resp.status_code)
    print("Content-Type:", resp.headers.get("Content-Type"))
    for enc in ["utf-8-sig", "big5", "cp950"]:
        try:
            print(resp.content.decode(enc)[:300])
            break
        except:
            pass
    print()