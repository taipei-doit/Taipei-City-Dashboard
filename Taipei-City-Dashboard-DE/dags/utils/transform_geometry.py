import geopandas as gpd
import pandas as pd
import pyproj
from geoalchemy2 import WKTElement
from numpy import nan
from shapely.geometry import MultiLineString
from shapely.geometry.multipolygon import MultiPolygon
from shapely.geometry.polygon import Polygon


def convert_3d_polygon_to_2d_polygon(geometry):
    """
    Convert 3D Multi/Polygons to 2D Multi/Polygons.
    """
    new_geo = []
    for p in geometry:
        if p.has_z:
            if p.geom_type == "Polygon":
                lines = [xy[:2] for xy in list(p.exterior.coords)]
                new_p = Polygon(lines)
                new_geo.append(new_p)
            elif p.geom_type == "MultiPolygon":
                new_multi_p = []
                for ap in p:
                    lines = [xy[:2] for xy in list(ap.exterior.coords)]
                    new_p = Polygon(lines)
                    new_multi_p.append(new_p)
                new_geo.append(MultiPolygon(new_multi_p))
    return new_geo


def convert_linestring_to_multilinestring(geo):
    """
    Convert LineString to MultiLineString.

    Example
    ----------
    line_a = LineString([[0,0], [1,1]])
    line_b = LineString([[1,1], [1,0]])
    multi_line = MultiLineString([line_a, line_b])
    convert_linestring_to_multilinestring(None)
    type(convert_linestring_to_multilinestring(multi_line))
    type(convert_linestring_to_multilinestring(line_a))
    """
    is_multistring = isinstance(geo, MultiLineString)
    is_na = pd.isna(geo)
    if (is_multistring) or (is_na):
        return geo
    else:
        return MultiLineString([geo])


def convert_polygon_to_multipolygon(geo):
    """
    Convert Polygon to MultiPolygon.

    Example
    ----------
    poly_a = Polygon([[0,0], [1,1], [1,0]])
    poly_b = Polygon([[1,0], [1,1], [2,0]])
    multi_poly = MultiPolygon([poly_a, poly_b])
    convert_polygon_to_multipolygon(None)
    type(convert_polygon_to_multipolygon(multi_poly))
    type(convert_polygon_to_multipolygon(poly_a))
    """
    is_multipolygon = isinstance(geo, MultiPolygon)
    is_na = pd.isna(geo)
    if (is_multipolygon) or (is_na):
        return geo
    else:
        return MultiPolygon([geo])


def add_point_wkbgeometry_column_to_df(
    data: pd.DataFrame,
    x: pd.Series,
    y: pd.Series,
    from_crs: int,
    to_crs=4326,
    is_add_xy_columns=True,
) -> gpd.GeoDataFrame:
    """
    Convert original DataFrame with x and y to GeoDataFrame with wkbgeometry.
    Input should be a pandas.DataFrame.
    Output will be a geopandas.GeoDataFrame and add 3 columns - wkb_geometry, lng, lat.

    Parameters
    ----------
    df: input DataFrame.
    x: x or lng.
    y: y or lat.
    from_crs: crs alias name as EPSG, commonly use 4326=WGS84 or 3826=TWD97
    to_crs: crs alias name as EPSG, default 4326.
    is_add_xy_columns: Add lng(x), lat(y) to output, defalut True.
        Only point type geometry will add column.
        Add these two column can benifit powerBI user.

    Example
    ----------
    x = pd.Series([262403.2367, 481753.6091, '', None])
    y = pd.Series([2779407.0527, 2914189.1837, None, ''])
    xx = pd.to_numeric(x, errors='coerce')
    gdf = add_point_wkbgeometry_column_to_df(data, x, y, from_crs=3826)
    gdf = add_point_wkbgeometry_column_to_df(data, x, y, from_crs=3826, is_add_xy_columns=False)
    """
    # covert column type
    x = pd.to_numeric(x, errors="coerce")
    y = pd.to_numeric(y, errors="coerce")
    geometry = gpd.points_from_xy(x, y)

    # make df to gdf
    df = data.copy()
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=f"EPSG:{from_crs}")
    if from_crs == to_crs:
        gdf = gdf.to_crs(epsg=from_crs)
        gdf = gdf.to_crs(epsg=to_crs)
    else:
        gdf = gdf.to_crs(epsg=to_crs)

    # add column
    if is_add_xy_columns:
        geo_type = gdf["geometry"].type.iloc[0]
        if geo_type == "Point":
            gdf["lng"] = gdf["geometry"].map(
                lambda ele: ele.x if not ele.is_empty else nan
            )
            gdf["lat"] = gdf["geometry"].map(
                lambda ele: ele.y if not ele.is_empty else nan
            )
    gdf["wkb_geometry"] = gdf["geometry"].apply(
        lambda x: WKTElement(x.wkt, srid=to_crs) if x is not None else None
    )

    return gdf


def convert_geometry_to_wkbgeometry(
    gdf: gpd.GeoDataFrame, from_crs: int, to_crs=4326
) -> gpd.GeoDataFrame:
    """
    Convert geometry column of GeoDataframe to wkbgeometry.

    Example 1
    ----------
    poly = pd.Series([
        Polygon([[262403, 2779407], [262404, 2779407], [262404, 2779408]]),
        Polygon([[262403, 2779407], [262405, 2779407], [262404, 2779408]]),
        Polygon([[262403, 2779407], [262403, 2779408], [262404, 2779408]]),
        Polygon([[262403, 2779407], [262404, 2779408], [262405, 2779408]])
    ])
    gdf = gpd.GeoDataFrame(data, geometry=poly, crs='EPSG:3826')
    gdf = convert_geometry_to_wkbgeometry(gdf, from_crs=3826)

    Example 2
    ----------
    # original
    gdata.crs = "EPSG:3826"
    gdata = gdata.to_crs(epsg=4326)
    gdata = gdata.rename(columns={'geometry': 'wkb_geometry'})
    gdata['wkb_geometry'] = gdata['wkb_geometry'].apply(
        lambda x: WKTElement(x.wkt, srid=4326) if x != None else None
    )
    gdata.drop(columns=['geometry'], inplace=True)
    # function
    gdata = convert_geometry_to_wkbgeometry(gdata, from_crs=3826, to_crs=4326)
    gdata.drop(columns=['geometry'], inplace=True)
    """
    # to make sure gdf is in `from_crs` projection
    gdf.crs = f"EPSG:{from_crs}"

    if from_crs == to_crs:
        gdf = gdf.to_crs(epsg=from_crs)
        gdf = gdf.to_crs(epsg=to_crs)
    else:
        gdf = gdf.to_crs(epsg=to_crs)
    gdf["wkb_geometry"] = gdf["geometry"].apply(
        lambda x: WKTElement(x.wkt, srid=to_crs) if x is not None else None
    )

    return gdf


def convert_twd97_to_wgs84(gdata, x_col: str, y_col: str) -> tuple:
    """
    Convert TWD97 to WGS84.

    Example
    ----------
    test = pd.DataFrame({
        "x": [304664, 304664, 304364],
        "y": [2770716, 2770616, 2770616]
    })
    lng, lat = convert_twd97_to_wgs84(test, x_col="x", y_col="y")
    print(lng)
    # output:
    # [25.0435983  25.04269551 25.04270632]

    print(lat)
    # output:
    # [121.54173557 121.5417316  121.53875864]
    """

    transformer = pyproj.Transformer.from_crs("EPSG:3826", "EPSG:4326")
    lat, lng = transformer.transform(gdata[x_col], gdata[y_col])
    return pd.Series(lng), pd.Series(lat)
