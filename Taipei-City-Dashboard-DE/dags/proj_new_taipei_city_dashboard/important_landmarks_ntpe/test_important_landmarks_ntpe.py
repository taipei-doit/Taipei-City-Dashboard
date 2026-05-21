import requests


def test_fetch_sample():
    url = "https://data.ntpc.gov.tw/api/datasets/6dcff24a-838c-40fb-a9df-f1160afafe84/json"
    r = requests.get(url, params={"page": 0, "size": 3}, timeout=60, verify=False)
    r.raise_for_status()
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
