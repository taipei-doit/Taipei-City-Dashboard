import json
import os
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

import fiona
import geopandas as gpd
import pandas as pd
import requests
from airflow.models import Variable
from settings.global_config import DATA_PATH, PROXIES
from utils.auth_tdx import TDXAuth


def download_file(
    file_name,
    url,
    is_proxy=False,
    is_verify=True,
    timeout: int = 60,
    file_folder=DATA_PATH,
):
    """
    Download file from `url` to `{DATA_PATH}/{file_name}`.

    Args:
        file_name: str, file name
        url: str, file url
        is_proxy: bool, whether use proxy
        is_verify: bool, whether verify ssl
        timeout: int, request timeout
        file_folder: str, file folder path

    Returns: str, full file path

    Example:
        ``` python
        # Read GeoJSON
        # GeoJSON is a special format of JSON that represents geographical data
        # The extension of a geoJSON file can be .geojson or .json.
        import geopandas as gpd
        from utils.extract_stage import download_file_by_filename

        URL = "https://pwdgis.taipei/wg/opendata/I0201-5.geojson"
        FILE_FOLDER = "your_foler_path"
        FILE_NAME = "goose_sanctuary.geojson"
        FILE_ENCODING = "UTF-8"

        local_file = download_file_by_filename(FILE_NAME, URL, file_folder=FILE_FOLDER)
        gdata = gpd.read_file(local_file, encoding=FILE_ENCODING, driver="GeoJSON")
        print(gdata)
        ```
        ```
        output:
        Id     名稱            面積    類型  集水區  物理型  水文HY  濱水植  水質WQ  生物BI  MIWC2017                                           geometry
        0   3  雁鴨保護區  1.799444e+06  重要濕地  NaN  NaN   NaN  NaN   NaN   NaN       NaN  MULTIPOLYGON (((121.51075 25.02214, 121.51083 ...
    ```
    """
    full_file_path = f"{file_folder}/{file_name}"
    # download file
    try:
        with requests.get(
            url,
            stream=True,
            proxies=PROXIES if is_proxy else None,
            verify=is_verify,
            timeout=timeout,
        ) as r:
            r.raise_for_status()
            with open(full_file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded {full_file_path} successfully.")
        return full_file_path
    except Exception as e:
        raise e


def unzip_file_to_target_folder(zip_file: str, unzip_path: str, encoding="UTF-8"):
    """
    Unzip .zip file from `zip_file` to `target_folder`.

    Args:
        zip_file: str, zip file path
        target_folder: str, target folder path
        encoding: str, file name encoding

    Returns: None

    Example:
        ``` python
        # Read Shapefile
        # Shapefile is a popular geospatial vector data format for geographic information system software.
        # The shapefile is a set of files with the same name but different extensions.
        # Usually, theses files been compressed into a zip file.
        import geopandas as gpd
        from utils.extract_stage import (
            download_file,
            unzip_file_to_target_folder,
        )
        from settings.global_config import DATA_PATH

        URL = r"https://data.moa.gov.tw/OpenData/GetOpenDataFile.aspx?id=I88&FileType=SHP&RID=27237"
        FILE_NAME = "debris_area.zip"
        unzip_path = f"{DATA_PATH}/debris_area"
        FILE_ENCODING = "UTF-8"

        zip_file = download_file(FILE_NAME, URL)
        unzip_file_to_target_folder(zip_file, unzip_path)
        target_shp_file = [f for f in os.listdir(unzip_path) if f.endswith("shp")][0]
        gdata = gpd.read_file(f"{unzip_path}/{target_shp_file}", encoding=FILE_ENCODING)
        ```
        ```
        >>> output:
                ID Debrisno  ... Dbno_old                                           geometry
        0        1  宜縣DF135  ...   宜蘭A089  LINESTRING (313537.820 2726900.950, 313625.420...
        1        2  宜縣DF131  ...   宜蘭A088  LINESTRING (319284.480 2727626.340, 319308.250...
        2        3  宜縣DF132  ...   宜蘭A087  LINESTRING (318877.260 2727421.020, 318878.620...
        3        4  宜縣DF133  ...   宜蘭A086  MULTILINESTRING ((317842.890 2725794.540, 3178...
        4        5  宜縣DF134  ...    宜蘭028  MULTILINESTRING ((315765.720 2726200.720, 3157...
        ...    ...      ...  ...      ...                                                ...
        1727  1728  花縣DF098  ...    花蓮020  LINESTRING (303782.140 2619541.820, 303857.320...
        1728  1729  花縣DF103  ...   花蓮A138  LINESTRING (302751.200 2607101.490, 302746.680...
        1729  1730  花縣DF104  ...   花蓮A139  LINESTRING (302677.050 2606792.820, 302667.830...
        1730  1731  花縣DF105  ...    花蓮025  MULTILINESTRING ((300594.180 2604587.920, 3005...
        1731  1732  花縣DF106  ...    花蓮026  MULTILINESTRING ((300470.400 2604218.870, 3004...

        [1732 rows x 31 columns]
        ```
    """
    unzip_dir = Path(unzip_path)

    # delete the unzip directory if it exists
    if unzip_dir.exists() and unzip_dir.is_dir():
        shutil.rmtree(unzip_dir)

    # create the unzip directory
    unzip_dir.mkdir(parents=True, exist_ok=False)

    # unzip file
    with zipfile.ZipFile(zip_file) as z:
        z.extractall(unzip_dir)
    print(f"Unzip {zip_file} to {unzip_path}")

    # rename with correct encoding
    if encoding != "UTF-8":
        for f_name in os.listdir(unzip_dir):
            try:
                new_name = f_name.encode("cp437").decode(encoding)
                os.rename(f"{unzip_dir}/{f_name}", f"{unzip_dir}/{new_name}")
            except Exception as e:
                print(f"Rename unzip file name `{f_name}`, failed with {e}")


def get_kml(url, dag_id, from_crs, **kwargs):
    """
    Download kml file from `url` to `{DATA_PATH}/{file_name}` and read it as geopandas dataframe.

    Note:
    Read kmz file is similar to read kml file. Kmz is a zip file including kml file.
    The steps to get kml file from kmz file:
    1. rename file extension from `{file_name}.kmz` to `{file_name}.zip`
    2. unzip `{file_name}.zip`
    3. read file `doc.kml` in the unzipped folder

    Args:
        url (str): The URL of the kml file.
        file_name (str): The file name of the kml file.
        from_crs (int): The CRS of the kml file.

    Example:
        ``` python
        from utils.extract_stage import get_kml

        URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=a69988de-6a49-4956-9220-40ebd7c42800"
        FILE_NAME = "urban_bike_path.kml"
        FROM_CRS = 4326

        res = get_kml(URL, dag_id, FROM_CRS)
        print(df.iloc[0])
        ```
        ```
        >>> print(df.iloc[0])
        Name                                                    三元街(西南側)
        Description      編號：TP2329 名稱：三元街(西南側) 縣市別：台北市 起點描述：南海路 迄點描述：泉州街
        geometry       LINESTRING Z (121.514241 25.027622 0, 121.5133...
        Name: 0, dtype: object
        ```


    """
    file_name = f"{dag_id}.kml"
    fiona.drvsupport.supported_drivers["KML"] = "rw"
    file = download_file(file_name, url, **kwargs)
    gdf = gpd.read_file(file, driver="KML")
    gdf = gpd.GeoDataFrame(gdf, crs=f"EPSG:{from_crs}")
    return gdf


def get_data_taipei_api(rid, timeout=60, output_format="json"):
    """
    Retrieve data from Data.taipei API by automatically traversing all data.
    (The Data.taipei API returns a maximum of 1000 records per request, so offset is used to
    obtain all data.)

    Args:
        rid (str): The resource ID of the dataset.
        timeout (int, optional): The timeout limit for the HTTP request in seconds. Defaults to 60.
        output_format (str, optional): The output format of the data. Defaults to "json", can be "json" or "dataframe".
            If "dataframe", the data will be returned as a pandas DataFrame and add column `data_time` from `_importdate`.

    Returns:
        Depends on `output_format`. If "json", return json. If "dataframe", return pandas dataframe.

    Example:
        ``` python
        from utils.extract_stage import get_data_taipei_api

        rid = "04a3d195-ee97-467a-b066-e471ff99d15d"
        res = get_data_taipei_api(rid)
        print(res)
    ```
    """
    url = f"https://data.taipei/api/v1/dataset/{rid}?scope=resourceAquire"
    response = requests.get(url, timeout=timeout)
    data_dict = response.json()
    count = data_dict["result"]["count"]
    res = []
    offset_count = int(count / 1000)
    for i in range(offset_count + 1):
        i = i * 1000
        url = f"https://data.taipei/api/v1/dataset/{rid}?scope=resourceAquire&offset={i}&limit=1000"
        response = requests.get(url, timeout=timeout)
        get_json = response.json()
        res.extend(get_json["result"]["results"])

    if output_format == "json":
        return res
    elif output_format == "dataframe":
        df = pd.DataFrame(res)
        df["data_time"] = df["_importdate"].apply(lambda x: x["date"])
        return df
    else:
        raise ValueError("output_format can only be 'json' or 'dataframe'.")


def get_data_taipei_file_last_modified_time(page_id, rank=0, timeout=30):
    """
    Request the file update time of given data.taipei page_id.
    file_last_modified is usually located at the end of the page, next to the download button.
    If a page has more than one file, you can specify the rank.

    Args:
        url (str): The URL of the data.taipei resource.
        rank (int, optional): The rank of the file last modified record. Defaults to 0 is top one.
        timeout (int, optional): The timeout limit for the HTTP request in seconds. Defaults to 30.

    Returns:
        str: The last modified time of the given data.taipei resource.

    Example:
        ``` python
        from utils.extract_stage import get_data_taipei_file_last_modified_time

        PAGE_ID = "4fefd1b3-58b9-4dab-af00-724c715b0c58"

        res = get_data_taipei_file_last_modified_time(PAGE_ID)
        print(res)
        ```
        ```
        >>> print(res)
        '2023-06-06 09:53:08'
        ```
    """
    url = f"https://data.taipei/api/frontstage/tpeod/dataset.view?id={page_id}"
    res = requests.get(url, timeout=timeout)
    if res.status_code != 200:
        raise ValueError(f"Request Error: {res.status_code}")

    data_info = json.loads(res.text)
    lastest_modeified_time = data_info["payload"]["resources"][rank]["last_modified"]
    return lastest_modeified_time


def get_data_taipei_page_change_time(page_id, rank=0, timeout=30):
    """
    Request the page change time of given data.taipei page_id.
    page_change_time is located at the left side tab 異動紀錄.
    The page_change_time usually have more than one record, so you can specify the rank.

    Args:
        url (str): The URL of the data.taipei resource.
        rank (int, optional): The rank of the page change time record. Defaults to 0 is lastest.
        timeout (int, optional): The timeout limit for the HTTP request in seconds. Defaults to 30.

    Returns:
        str: The page change time of the given data.taipei resource.

    Example:
        ``` python
        from utils.extract_stage import get_data_taipei_page_change_time

        PAGE_ID = "4fefd1b3-58b9-4dab-af00-724c715b0c58"

        res = get_data_taipei_page_change_time(PAGE_ID)
        print(res)
        ```
        ```
        >>> print(res)
        2023-09-08 10:02:06
        ```
    """
    url = f"https://data.taipei/api/frontstage/tpeod/dataset/change-history.list?id={page_id}"
    res = requests.get(url, timeout=timeout)
    if res.status_code != 200:
        raise ValueError(f"Request Error: {res.status_code}")

    update_history = json.loads(res.text)
    lastest_update = update_history["payload"][rank]
    lastest_update_time = lastest_update.split("更新於")[-1]
    return lastest_update_time.strip()


def _check_request_status(res):
    if res.status_code != 200:
        raise RuntimeError("Error: {res.status_code}")

    try:
        res.json()
    except json.decoder.JSONDecodeError as e:
        raise RuntimeError(f"Can not decode JSON, msg is `{res.text}`") from e


def get_moenv_json_data(
    dataset_code,
    filters_query=None,
    sort_query=None,
    is_test=False,
    is_proxy=False,
    timeout=60,
):
    """
    Get data from Ministry of Environment Open Data Platform API.
    Detail API parameters description can be found in the following link:
    https://drive.google.com/file/d/13kPG4SJ_4IQI2mVBK_-i422U41BUb-d5/view

    Args:
        dataset_code (str): The dataset code.
        filters_query (str): The filter query.
        sort_query (str): The sort query.
        is_test (bool): If True, only get 10 records.
        timeout (int): The timeout for the request.

    Returns:
        list: The list of records.

    Example:
    ``` python
    temp = get_moenv_json_data("AQX_P_136", is_test=True)
    print(temp[0])
    ```

    ``` python
    >>> print(temp[0])
        {'siteid': '64', 'sitename': '陽明', 'county': '臺北市', 'itemid': '11', 'itemname': '風向',
        'itemengname': 'WIND_DIREC', 'itemunit': 'degrees', 'monitordate': '2024-05-31 13:00',
        'concentration': '50'}
    ```
    """
    api_key = Variable.get("MOENV_API_KEY")

    url = (
        f"https://data.moenv.gov.tw/api/v2/{dataset_code}?format=json&api_key={api_key}"
    )

    if filters_query:
        url += f"&filters={filters_query}"

        if sort_query:
            url += f"&sort={sort_query}"

    if is_test:
        limit = 10
        offset = [0]
    else:
        res = requests.get(
            f"{url}&offset=0&limit=1",
            proxies=PROXIES if is_proxy else None,
            timeout=timeout,
        )
        _check_request_status(res)
        total_records = res.json()["total"]
        limit = 1000
        offset = [i for i in range(0, int(total_records), limit)]

    results = []
    for o in offset:
        res = requests.get(
            f"{url}&offset={o}&limit={limit}",
            proxies=PROXIES if is_proxy else None,
            timeout=timeout,
        )
        _check_request_status(res)
        results.extend(res.json()["records"])
        time.sleep(0.1)

    return results


def get_shp_file(
    url, dag_id, from_crs, encoding="UTF-8", file_ends_with=".shp", **kwargs
):
    """
    Download zip from url then unzip then read first shp file.
    Return geopandas dataframe.

    Args:
        url (str): The url of the shapefile.
        dag_id (str): The DAG ID.
        from_crs (int): The CRS of the shapefile.
        encoding (str, optional): The encoding of the shapefile. Defaults to "UTF-8".
        is_proxy (bool, optional): Whether to use a proxy. Defaults to False.
        file_ends_with (str, optional): The file extension of the shapefile. Defaults to ".shp".
            If your folder have multiple shapefiles, you can specify the `file_ends_with` to get the target file.

    Returns:
        geopandas.GeoDataFrame: The geopandas dataframe.

    Example:
        ``` python
        from utils.extract_stage import get_shp_file

        dag_id = 'R0020'
        URL = "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid=e7a23ebc-f56b-424f-8073-f2469dc99c6d"
        FROM_CRS = 3826
        ENCODING = "UTF-8"
        raw_data = get_shp_file(URL, dag_id, FROM_CRS, encoding=ENCODING)
        print(raw_data.iloc[0])
        ```

        ``` python
        >>> print(raw_data.iloc[0])
        MSISID                                       5154-NH-GDS-0012
        LEVEL                                                     第五類
        URL         http://210.69.23.171/MSIS/PDF/5154-NH-GDS-0012...
        geometry    LINESTRING Z (312792.6854118169 2775798.500770...
        Name: 0, dtype: object
        ```
    """
    filename = f"{dag_id}.zip"
    unzip_path = f"{DATA_PATH}/{dag_id}"
    zip_file = download_file(filename, url, **kwargs)
    unzip_file_to_target_folder(zip_file, unzip_path, encoding=encoding)

    # walk through the unzip folder to get the first shp file
    shp_file = None
    for root, dirs, files in os.walk(unzip_path):
        for file in files:
            if file.endswith(file_ends_with):
                shp_file = os.path.join(root, file)

    if shp_file is None:
        raise ValueError(f"No .shp files found in {unzip_path}")

    gdf = gpd.read_file(shp_file, encoding=encoding, from_crs=from_crs)
    print(f"Read {shp_file} successfully.")
    return gdf


def get_tdx_data(url, is_proxy=False, timeout=60, output_format="json"):
    """
    Request data from TDX API and return with `output_format`.

    Args:
        url (str): The URL of the TDX API.
        is_proxy (bool, optional): Whether to use a proxy. Defaults to False.
        timeout (int, optional): The timeout for the request. Defaults to 60.
        output_format (str, optional): The output format of the data. Defaults to "json". Can be "json", "dataframe", or "raw".

    Returns:
        Depends on `output_format`. If "json", return json. If "dataframe", return pandas dataframe. If "raw", return request.response.

    Example:
        ``` python
        from utils.extract_stage import get_tdx_data

        URL = r"https://tdx.transportdata.tw/api/basic/v2/Bike/Station/City/Taipei?%24format=JSON"
        raw_data = get_tdx_data(URL, output_format='dataframe')
        print(raw_data.iloc[0])
        ```
    """
    # get token
    tdx = TDXAuth()
    token = tdx.get_token(is_proxy=is_proxy, timeout=timeout)

    # get data
    headers = {"authorization": f"Bearer {token}"}
    response = requests.get(
        url, headers=headers, proxies=PROXIES if is_proxy else None, timeout=timeout
    )
    if response.status_code != 200:
        raise ValueError(f"Request failed! status: {response.status_code}")

    if output_format == "json":
        return response.json()
    elif output_format == "dataframe":
        return pd.DataFrame(response.json())
    elif output_format == "raw":
        return response
    else:
        raise ValueError("Invalid output_format.")


def get_json_file(url, dag_id, encoding="UTF-8", output_format="json", **kwargs):
    """
    Download JSON file and return with `output_format`.

    Args:
        file_name (str): The file name of the JSON file.
        url (str): The URL of the JSON file.
        encoding (str, optional): The encoding of the JSON file. Defaults to "UTF-8".
        output_format (str, optional): The output format of the data. Defaults to "json". Can be "json", "dataframe".

    Returns:
        Depends on `output_format`. If "json", return json. If "dataframe", return pandas dataframe.

    Example:
        ``` python
        from utils.extract_stage import get_json_file

        DAG_ID = 'D050102_2'
        URL = "https://tppkl.blob.core.windows.net/blobfs/TaipeiTree.json"
        raw_data = get_json_file(
            URL, DAG_ID, timeout=None, is_proxy=True, output_format="dataframe"
        )
        print(raw_data.iloc[0])
        ```

        ``` python
        >>> print(raw_data.iloc[0])
        TreeID                 NG0590010038
        Dist                            士林區
        Region                       環河北路三段
        RegionRemark                  西側人行道
        TreeType                        白千層
        Diameter                       31.0
        TreeHeight                    11.62
        SurveyDate               2016-05-21
        TWD97X                     300889.8
        TWD97Y                   2775475.49
        UpdDate         2024-05-10 14:03:21
        Name: 0, dtype: object
        ```
    """
    file_name = f"{dag_id}.json"
    local_file = download_file(file_name, url, **kwargs)
    if not local_file:
        return False
    with open(local_file, encoding=encoding) as json_file:
        res = json.load(json_file)

    if output_format == "json":
        return res
    elif output_format == "dataframe":
        return pd.DataFrame(res)
    else:
        raise ValueError("Invalid output_format.")


def get_geojson_file(url, dag_id, from_crs, encoding="UTF-8", **kwargs):
    """
    Download GeoJSON file and return with geopandas dataframe.

    Args:
        url (str): The URL of the GeoJSON file.
        dag_id (str): The DAG ID.
        from_crs (int): The CRS of the GeoJSON file.
        encoding (str, optional): The encoding of the GeoJSON file. Defaults to "UTF-8".

    Returns:
        geopandas.GeoDataFrame: The geopandas dataframe.

    Example:
        ``` python
        from utils.extract_stage import get_geojson_file

        URL = "https://soil.taipei/Taipei/Main/pages/TPLiquid_84.GeoJSON"
        FROM_CRS = 4326
        DAG_ID = 'D050101_1' 
        raw_data = get_geojson_file(URL, DAG_ID, FROM_CRS)
        print(raw_data.iloc[0])
        ```

        ``` python
        >>> print(raw_data.iloc[0])
        class                                                       1
        geometry    MULTIPOLYGON (((121.50338406082561 25.13630313...
        Name: 0, dtype: object
        ```
    """
    file_name = f"{dag_id}.geojson"
    local_file = download_file(file_name, url, **kwargs)
    gdf = gpd.read_file(
        local_file, encoding=encoding, driver="GeoJSON", from_crs=from_crs
    )
    print(f"Read {local_file} successfully.")
    return gdf
