import json
from pathlib import Path

import requests


def _fetch_rows():
    config_path = Path(__file__).with_name("job_config.json")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    source_url = config["data_infos"]["source"]
    print(f"source_url={source_url}")

    resp = requests.get(source_url, timeout=30)
    resp.raise_for_status()

    data = resp.json()

    if isinstance(data, dict):
        return (
            data.get("result", {}).get("results")
            or data.get("result", {}).get("records")
            or data.get("data")
            or data.get("records")
            or []
        )

    if isinstance(data, list):
        return data

    return []


def test_source_url_reachable():
    rows = _fetch_rows()
    assert len(rows) > 0, "API reachable but no rows found"
    print(f"reachable, sample keys: {list(rows[0].keys())[:10]}")


if __name__ == "__main__":
    test_source_url_reachable()
    print("All tests passed")
