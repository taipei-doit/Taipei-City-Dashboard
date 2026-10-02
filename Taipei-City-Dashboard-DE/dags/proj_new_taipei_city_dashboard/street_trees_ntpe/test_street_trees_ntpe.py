import requests


def test_fetch_sample():
    url = "https://data.ntpc.gov.tw/api/datasets/57f99afb-94e2-4e67-9de7-961f5e9a9e18/json"
    r = requests.get(url, params={"page": 0, "size": 3}, timeout=60, verify=False)
    r.raise_for_status()
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
