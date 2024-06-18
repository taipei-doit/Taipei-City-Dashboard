import time

import geopandas as gpd
from geoalchemy2 import Geometry
from sqlalchemy.sql import text as sa_text
from utils.get_time import get_tpe_now_time_str


def update_lasttime_in_data_to_dataset_info(
    engine, airflow_dag_id, lasttime_in_data=None
):
    '''
    Update lasttime_in_data to dataset_info.

    Args:
    airflow_dag_id : str.
    lasttime_in_data: str format 'yyyy-MM-dd HH:mm:ssTZH', for example '2024-02-15 16:40:54+08'.
        Default is None. If not provided, current time with timezone Asia/Taipei will be used.
        If the input is not a string, it will using str() attempt to convert it to a string.
        If TZH is not included in the string, it will be assumed to be UTC+0.
    engine : sqlalchemy.engine.base.Engine. Psql engine.

    Use case:
    # original
    airflow_dag_id = 'test_123'
    lasttime_in_data = df["Date"].max()
    sql = f"""
        UPDATE dataset_info
        SET lasttime_in_data = TO_TIMESTAMP('{lasttime_in_data}', 'yyyy-MM-ddThh24:mi:ssTZH')
        WHERE airflow_dag_id = '{airflow_dag_id}'
    """
    conn = engine.connect()
    conn.execute_sql(sa_text(sql))
    conn.close()
    # function
    update_lasttime_in_data_to_dataset_info(
        engine, airflow_dag_id='test_123', lasttime_in_data=df["Date"].max()
    )
    '''
    # check lasttime_in_data given
    if lasttime_in_data is None:
        lasttime_in_data = get_tpe_now_time_str(is_with_tz=True)
    else:
        # convert to string if not
        if not isinstance(lasttime_in_data, str):
            lasttime_in_data = str(lasttime_in_data)
            print(
                "lasttime_in_data is not a string, it has been converted to a string."
            )

    # main
    sql = f"""
        UPDATE dataset_info
        SET lasttime_in_data = TO_TIMESTAMP('{lasttime_in_data}', 'yyyy-MM-dd hh24:mi:ssTZH')
        WHERE airflow_dag_id = '{airflow_dag_id}'
    """
    conn = engine.connect()
    conn.execute(sa_text(sql).execution_options(autocommit=True))
    conn.close()

    # print
    print(f"Last time in data been updated to {lasttime_in_data}.")


def drop_duplicated_before_saving():
    pass


def drop_duplicated_after_saving(
    engine, psql_table: str, criterion: str, comparing_col: str = "ogc_fid"
):
    '''
    Drop duplicated after saving data to psql_table.

    Args:
    engine : sqlalchemy.engine.base.Engine.
    psql_table : str. Psql table name.
    criterion : str. The criterion for dropping duplicated.
        For example, 'AND a."FNumber" = b."FNumber"'. Can't contain ';'.
        Since the criterion will be used in a sql command, it should be a valid sql command and
        always start with 'AND'.
    comparing_col : str.  Default is 'ogc_fid'.
        The comparing_col is used for deciding which row to keep.
        If two rows have the same comparing_col, the row with the bigger comparing_col will be kept.

    Use case:
    # original
    psql_table_name = 'test_123'
    sql = f"""
        DELETE FROM {psql_table_name} a USING {psql_table_name} b
        WHERE a.ogc_fid < b.ogc_fid
            AND a."FNumber" = b."FNumber"
        """
    conn = engine.connect()
    conn.execute(sql)
    conn.close()
    # funciton
    criterion = 'AND a."FNumber" = b."FNumber"'
    drop_duplicated_after_saving(
        engine,
        psql_table='test_123',
        criterion='AND a."FNumber" = b."FNumber"',
        comparing_col='ogc_fid'
    )
    '''
    # criterion cant contain ';'
    if ";" in criterion:
        raise ValueError('`criterion` can not contain ";".')

    start_time = time.time()

    # main
    sql = f"""
        DELETE FROM {psql_table} a
        USING {psql_table} b
        WHERE a.{comparing_col} < b.{comparing_col}
            {criterion}
    """
    conn = engine.connect()
    conn.execute(sa_text(sql).execution_options(autocommit=True))
    conn.close()

    # print
    cost_time = time.time() - start_time
    print(f"Duplicated been dropped in {psql_table}, cost time: {cost_time:.2f}s.")


def save_dataframe_to_postgresql(
    engine, data, load_behavior: str, default_table: str, history_table: str = None
):
    """
    Save pd.DataFrame to psql.
    A high-level API for pd.DataFrame.to_psql with `index=False` and `schema='public'`.
    If the data is gpd.GeoDataFrame, use function `save_geodataframe_to_postgresql` instead.

    Args:
    engine : sqlalchemy.engine.base.Engine.
    data : pd.DataFrame. Data to be saved.
    load_behavior : str. Save mode, should be one of `append`, `replace`, `current+history`.
        `append`: Just append new data to the `default_table`.
        `replace`: Truncate the `default_table` and append new data.
        `current+history`: The current+history design is intended to preserve historical records
            while simultaneously maintaining the most recent data. This proces will truncate
            the `default_table` and append the new data into it, then append the new data
            to `history_table`.
    default_table : str. Default table name.
    history_table : str. History table name, only used when load_behavior is `current+history`.

    Use case:
    # original
    table_name = 'test_123'
    with engine.connect() as conn:
        sql = f'TRUNCATE TABLE {table_name}'
        conn.execute(sa_text(sql).execution_options(autocommit=True))
        mapping_table.to_sql(table_name, conn, if_exists='append', index=False, schema='public')
        conn.commit()
    # function
    save_dataframe_to_postgresql(
        engine, data=mapping_table, load_behavior='replace', current_table='test_123',
    )
    """
    # check data type
    if isinstance(data, gpd.GeoDataFrame):
        raise ValueError(
            "Data type is gpd.GeoDataFrame, use function `save_geodataframe_to_postgresql` instead."
        )

    is_column_include_geometry = data.columns.isin(["wkb_geometry", "geometry"])
    if any(is_column_include_geometry):
        raise ValueError(
            """
            Column name contains `wkb_geometry` or `geometry`, it should be a GeoDataFrame.
            Please use function `save_geodataframe_to_postgresql` instead.
        """
        )

    start_time = time.time()

    # main
    conn = engine.connect()
    if load_behavior == "append":
        data.to_sql(
            default_table, conn, if_exists="append", index=False, schema="public"
        )
    elif load_behavior == "replace":
        conn.execute(
            sa_text(f"TRUNCATE TABLE {default_table}").execution_options(
                autocommit=True
            )
        )
        data.to_sql(
            default_table, conn, if_exists="append", index=False, schema="public"
        )
    elif load_behavior == "current+history":
        if history_table is None:
            raise ValueError(
                "history_table should be provided when load_behavior is `current+history`."
            )
        conn.execute(
            sa_text(f"TRUNCATE TABLE {default_table}").execution_options(
                autocommit=True
            )
        )
        data.to_sql(
            default_table, conn, if_exists="append", index=False, schema="public"
        )
        data.to_sql(
            history_table, conn, if_exists="append", index=False, schema="public"
        )
    else:
        raise ValueError(
            "load_behavior should be one of `append`, `replace`, `current+history`."
        )
    conn.close()

    # print
    cost_time = time.time() - start_time
    print(f"Data been saved, cost time: {cost_time:.2f}s.")


def save_geodataframe_to_postgresql(
    engine,
    gdata,
    load_behavior: str,
    geometry_type: str,
    default_table: str,
    history_table: str = None,
    geometry_col: str = "wkb_geometry",
):
    """
    Save gpd.GeoDataFrame to psql.
    A high-level API for gpd.GeoDataFrame.to_psql with `index=False` and `schema='public'`.
    The geometry column should be in WKB format, and EPSG:4326 is used.
    If the data is pd.DataFrame, use function `save_dataframe_to_postgresql` instead.

    Args:
    engine : sqlalchemy.engine.base.Engine.
    gdata : gpd.GeoDataFrame. Data with geometry to be saved.
    load_behavior : str. Save mode, should be one of `append`, `replace`, `current+history`.
        `append`: Just append new data to the `default_table`.
        `replace`: Truncate the `default_table` and append new data.
        `current+history`: The current+history design is intended to preserve historical records
            while simultaneously maintaining the most recent data. This proces will truncate
            the `default_table` and append the new data into it, then append the new data
            to `history_table`.
    default_table : str. Default table name.
    history_table : str. History table name, only used when load_behavior is `current+history`.
    geometry_type : str. Geometry type, should be one of the following:
        ['Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon',
        'LineStringZ', 'MultiLineStringZ', 'PolygonZ', 'MultiPolygonZ', 'GeometryCollection'].
    geometry_col : str. The geometry column name. Default is 'wkb_geometry'.
        *The data in the column should be in WKB format.
        “Well-known binary” (WKB) is a scheme for writing a simple features geometry into a
        platform-independent array of bytes, usually for transport between systems or between
        programs. By using WKB, systems can avoid exposing their particular internal implementation
        of geometry storage, for greater overall interoperability.

    Use case:
    # original
    psql_table = 'test_123'
    history_table = 'test_123_history'
    with engine.begin() as conn:
        conn.execute(sa_text(f'TRUNCATE TABLE {psql_table}').execution_options(autocommit=True))
        df.to_sql(
            psql_table, conn, if_exists='append',
            index=False, schema='public',
            dtype={'wkb_geometry': Geometry('Polygon', srid= 4326)}
        )
        df.to_sql(
            history_table, conn, if_exists='append',
            index=False, schema='public',
            dtype={'wkb_geometry': Geometry('Polygon', srid= 4326)}
        )
    # function
    save_geodataframe_to_postgresql(
        engine, gdata=gdf, load_behavior='current+history',
        default_table='test_123', history_table='test_123_history',
        geometry_type='Polygon', geometry_col='wkb_geometry'
    )
    """
    # Data type should not been checked, because the process of geometry to wkb_geometry.
    # The process could generate invalid geometry, so data type cant be converted to GeoDataFrame.

    # check geometry type is valid
    white_list = [
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
        "LineStringZ",
        "MultiLineStringZ",
        "PolygonZ",
        "MultiPolygonZ",
        "GeometryCollection",
    ]
    if geometry_type not in white_list:
        raise ValueError(
            f"geometry_type should be one of {white_list}, but got {geometry_type}."
        )

    start_time = time.time()

    # main
    conn = engine.connect()
    if load_behavior == "append":
        gdata.to_sql(
            default_table,
            conn,
            if_exists="append",
            index=False,
            schema="public",
            dtype={geometry_col: Geometry(geometry_type, srid=4326)},
        )
    elif load_behavior == "replace":
        conn.execute(
            sa_text(f"TRUNCATE TABLE {default_table}").execution_options(
                autocommit=True
            )
        )
        gdata.to_sql(
            default_table,
            conn,
            if_exists="append",
            index=False,
            schema="public",
            dtype={geometry_col: Geometry(geometry_type, srid=4326)},
        )
    elif load_behavior == "current+history":
        if (history_table is None) or (history_table == ""):
            raise ValueError(
                "history_table should be provided when load_behavior is `current+history`."
            )
        conn.execute(
            sa_text(f"TRUNCATE TABLE {default_table}").execution_options(
                autocommit=True
            )
        )
        gdata.to_sql(
            default_table,
            conn,
            if_exists="append",
            index=False,
            schema="public",
            dtype={geometry_col: Geometry(geometry_type, srid=4326)},
        )
        gdata.to_sql(
            history_table,
            conn,
            if_exists="append",
            index=False,
            schema="public",
            dtype={geometry_col: Geometry(geometry_type, srid=4326)},
        )
    else:
        raise ValueError(
            "load_behavior should be one of `append`, `replace`, `current+history`."
        )
    conn.close()

    # print
    cost_time = time.time() - start_time
    print(f"GeoData been saved, cost time: {cost_time:.2f}s.")
