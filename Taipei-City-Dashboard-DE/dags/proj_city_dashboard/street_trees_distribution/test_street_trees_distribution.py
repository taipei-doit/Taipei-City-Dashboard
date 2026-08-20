import requests


def test_source_available():
    """Check that the dataset landing page / package is reachable."""
    url = "https://data.nat.gov.tw/dataset/146760"
    r = requests.head(url, timeout=20)
    r.raise_for_status()
    assert r.status_code in (200, 301, 302)
