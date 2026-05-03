

包含 3 維 `Polygon` 轉成 2 維、`LineString` 轉成 `MultiLineString`、`Polygon` 轉成 `MultiPolygon`、根據 x, y 加入 `Point` 欄位、地理空間資訊轉成 WKBGeometry 格式。其中有部分為子函式，以下將不會說明子函式。

可在 `/dag/utils/transform_geometry.py` 查看相關程式碼。

> **w01**
> 務必確認你已經查看[下載並設定專案](/data-end/project-setup)章節並設置完成。

> **w02**
> 若開發者在 Airflow 環境想單獨測試以下程式碼，需先執行以下程式碼取得環境設定。
> ``` python
> from airflow import DAG
> ```

> **w03**
> 若開發者需要在非 Airflow 的環境測試以下程式碼，需添加以下幾行程式，以確保將本專案的路徑加入環境變數，從而能找到 `utils` 與 `settings` 等資料夾：
> ``` python
> import os
> import sys
>
> dags_path = os.path.join(os.getcwd(), 'dags') 
> sys.path.append(dags_path)
> ```

## 函式說明

### -函式 convert_geometry_to_wkbgeometry(gdf, from_crs)

對包含 `geometry` 欄位的 gpd.geoDataFrame 增加一個 WKBGeometry 格式的`wkb_geometry`欄位。輸出結果固定為 `EPSG:4326`，也就是 `WGS84` 坐標系。

```python
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from utils.transform_geometry import convert_geometry_to_wkbgeometry

data = pd.DataFrame({
    'id': [1, 2],
    'attribute': ['A', 'B']
})
poly = pd.Series([
    Polygon([[262403, 2779407], [262404, 2779407], [262404, 2779408]]),
    Polygon([[262403, 2779407], [262405, 2779407], [262404, 2779408]])
])
gdf = gpd.GeoDataFrame(data, geometry=poly, crs='EPSG:3826')
gdf = convert_geometry_to_wkbgeometry(gdf, from_crs=3826)
print(gdf.iloc[0])
```

```
>>> print(gdf.iloc[0])
id                                                              1
attribute                                                       A
geometry        POLYGON ((121.12299765144614 25.12299971980088...
wkb_geometry    POLYGON ((121.12299765144614 25.12299971980088...
Name: 0, dtype: object
```

### -函式 add_point_wkbgeometry_column_to_df(data, x, y, from_crs)

將 x, y 資料製成一個名為 `geometry` 的包含 `Point` 地理空間資料的欄位。同時加入另一個名為 `wkb_geometry` 的表示同樣資料但格式為 WKBGeometry 的欄位。

```python
import pandas as pd
import geopandas as gpd
from utils.transform_geometry import add_point_wkbgeometry_column_to_df

data = pd.DataFrame({
    'id': [1, 2],
    'attribute': ['A', 'B']
})
x = pd.Series([262403.2367, None])
y = pd.Series([2779407.0527, ''])
gdf = add_point_wkbgeometry_column_to_df(data, x, y, from_crs=3826)
print(gdf.iloc[0])
```

```
>>> print(gdf.iloc[0])
id                                                          1
attribute                                                   A
geometry        Point (121.12299999921674 25.123000193639967)
lng                                                   121.123
lat                                                    25.123
wkb_geometry    Point (121.12299999921674 25.123000193639967)
Name: 0, dtype: object
```

### -函式 convert_3d_polygon_to_2d_polygon(geometry)

將包含 z 軸的 3D `Polygon` 轉成沒有 z 軸的 2D `Polygon`。

```python
import geopandas as gpd
from shapely.geometry import Polygon
from utils.transform_geometry import convert_3d_polygon_to_2d_polygon

polygon_with_z = Polygon([(0, 0, 0), (1, 0, 1), (1, 1, 2), (0, 1, 3), (0, 0, 0)])
geos_polyz = gpd.GeoSeries([polygon_with_z, polygon_with_z])
print(geos_polyz)
# >>> print(geos_polyz)
# 0    POLYGON Z ((0.00000 0.00000 0.00000, 1.00000 0...
# 1    POLYGON Z ((0.00000 0.00000 0.00000, 1.00000 0...
# dtype: geometry

geos_poly = geos_polyz.apply(convert_3d_polygon_to_2d_polygon)
print(geos_poly)
# >>> print(geos_poly)
# 0    POLYGON ((0.00000 0.00000, 1.00000 0.00000, 1....
# 1    POLYGON ((0.00000 0.00000, 1.00000 0.00000, 1....
# dtype: geometry
```

### -函式 convert_linestring_to_multilinestring(geo)

將 `LineString` 修改為 `MultiLineString`，通常是因為欄位值混雜此兩種格式，修改為同一種格式以符合資料庫欄位型態。範例如下：

```python
import geopandas as gpd
from shapely.geometry import LineString
from utils.transform_geometry import convert_linestring_to_multilinestring

geos = gpd.GeoSeries([LineString([[0,0], [1,1]]), LineString([[0,0], [1,1]])])

geos_mline = geos.apply(convert_linestring_to_multilinestring)
print(geos_mline)
```

```
>>> print(geos_mline)
0    MULTILINESTRING ((0.00000 0.00000, 1.00000 1.0...
1    MULTILINESTRING ((0.00000 0.00000, 1.00000 1.0...
dtype: geometry
```

### -函式 convert_polygon_to_multipolygon(geo)

將 `Polygon` 修改為 `MultiPolygon`，通常是因為欄位值混雜此兩種格式，修改為同一種格式以符合資料庫欄位型態。

```python
import geopandas as gpd
from shapely.geometry import LineString
from utils.transform_geometry import convert_polygon_to_multipolygon

poly = Polygon([[0,0], [1,1], [1,0]])
geos = gpd.GeoSeries([poly, poly])
geos_mpoly = geos.apply(convert_polygon_to_multipolygon)
print(geos_mpoly)
```

```
>>> print(geos_mpoly)
0    MULTIPOLYGON (((0.00000 0.00000, 1.00000 1.000...
1    MULTIPOLYGON (((0.00000 0.00000, 1.00000 1.000...
dtype: geometry
```
