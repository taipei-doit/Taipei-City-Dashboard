import requests


SOURCE_URL = "https://data.ntpc.gov.tw/api/datasets/5fe3a136-29cc-4695-a17e-6636a32c3342/json"


def test_source_url_reachable():
    res = requests.get(SOURCE_URL, params={"page": 0, "size": 1}, timeout=60)
    res.raise_for_status()
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "data.ntpc.gov.tw" in SOURCE_URL
