import requests


def test_ckan_package_and_resource():
    pkg_url = "https://data.gov.tw/api/3/action/package_show?id=121225"
    r = requests.get(pkg_url, timeout=10)
    r.raise_for_status()
    pkg = r.json()
    resources = pkg.get("result", {}).get("resources", [])
    assert resources, "No resources found in CKAN package 121225"

    # pick geojson if available
    resource = None
    for res in resources:
        fmt = (res.get("format") or "").lower()
        url = res.get("url") or ""
        if "geojson" in fmt or url.endswith(".geojson"):
            resource = res
            break
    if resource is None:
        resource = resources[0]

    resource_url = resource.get("url")
    assert resource_url, "Resource has no url"

    # Verify resource is reachable
    rh = requests.head(resource_url, timeout=10)
    rh.raise_for_status()
