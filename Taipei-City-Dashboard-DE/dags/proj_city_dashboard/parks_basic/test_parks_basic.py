import requests


def test_parks_api_reachable():
    api_url = "https://parks.gov.taipei/parks/api/"
    r = requests.get(api_url, timeout=10)
    r.raise_for_status()
    j = r.json()
    assert isinstance(j, list) and len(j) > 0, "parks API did not return a non-empty list"
