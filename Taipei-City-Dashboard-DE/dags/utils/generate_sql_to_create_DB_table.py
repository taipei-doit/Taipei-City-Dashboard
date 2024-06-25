def generate_sql_to_define_column(
    table_name, col_map, is_add_ogc_fid=True, is_add_mtime=True, is_add_ctime=True
):
    """
    Generate SQL to define columns by converting the input dictionary into SQL text.

    Args:
        table_name (str): The name of the table.
        col_map (dict): A dictionary containing column names as keys and column types as values.
        is_add_ogc_fid (bool): Whether to add the OGC_FID column. Default is True.
        is_add_mtime (bool): Whether to add the MTIME column. Default is True.
        is_add_ctime (bool): Whether to add the CTIME column. Default is True.

    Returns:
        str: SQL text defining the columns.

    ---- use case
    column_map = {
        'id': 'serial',
        'name': 'varchar(255)',
        'age': 'integer'
    }
    column_define_sql = generate_sql_to_define_column(col_map)
    column_define_sql = generate_sql_to_define_column(col_map, is_add_ogc_fid=True)
    column_define_sql = generate_sql_to_define_column(col_map, is_add_mtime=True)
    column_define_sql = generate_sql_to_define_column(col_map, is_add_ctime=True)
    column_define_sql = generate_sql_to_define_column(
        col_map, is_add_ogc_fid=True, is_add_ctime=True, is_add_mtime=True
    )
    """
    col_sql = ""
    for _col, _type in col_map.items():
        _text = f"        {_col} {_type},\n"
        col_sql += _text
    col_sql = col_sql[:-2]

    if is_add_ctime:
        mtime_sql = (
            ",\n        _ctime timestamp with time zone DEFAULT CURRENT_TIMESTAMP"
        )
        col_sql += mtime_sql

    if is_add_mtime:
        ctime_sql = (
            ",\n        _mtime timestamp with time zone DEFAULT CURRENT_TIMESTAMP"
        )
        col_sql += ctime_sql

    if is_add_ogc_fid:
        ofc_fid_sql = f"""
            \n        ,ogc_fid integer NOT NULL DEFAULT nextval('{table_name}_ogc_fid_seq'::regclass),
            \n        CONSTRAINT {table_name}_pkey PRIMARY KEY (ogc_fid)
        """
        col_sql += ofc_fid_sql

    return col_sql


def generate_sql_to_create_db_table(
    table_name,
    col_map,
    is_add_mtime=True,
    is_add_ctime=True,
    is_add_ogc_fid=True,
    is_grant_socl_reader=False,
):
    """
    Generate SQL to create a database table based on the table name and column definitions.

    Args:
        table_name (str): The name of the table.
        col_map (dict): A dictionary containing column names as keys and column types as values.
        is_add_mtime (bool): Whether to add the MTIME column. Default is True.
        is_add_ctime (bool): Whether to add the CTIME column. Default is True.
        is_add_ogc_fid (bool): Whether to add the OGC_FID column. Default is True.
        is_grant_socl_reader (bool): Whether to grant SELECT permission to socl_reader. Default is False.

    Returns:
        str: SQL text to create the database table.
    """
    sql = ""

    col_sql = generate_sql_to_define_column(
        table_name,
        col_map,
        is_add_mtime=is_add_mtime,
        is_add_ctime=is_add_ctime,
        is_add_ogc_fid=is_add_ogc_fid,
    )

    create_table_sql = f"""
    -- create table
    CREATE TABLE IF NOT EXISTS public.{table_name}
    (
        {col_sql}
    )
    WITH (
        OIDS = FALSE
    )
    TABLESPACE pg_default;
    """

    grant_table_sql = f"""
    
    -- grant table
    ALTER TABLE IF EXISTS public.{table_name} OWNER to postgres;
    GRANT ALL ON TABLE public.{table_name} TO postgres WITH GRANT OPTION;
    """

    create_mtime_trigger_sql = f"""
    
    -- create mtime trigger
    CREATE TRIGGER {table_name}_mtime
        BEFORE INSERT OR UPDATE 
        ON public.{table_name}
        FOR EACH ROW
        EXECUTE PROCEDURE public.trigger_set_timestamp();
    """

    create_sequnce_sql = f"""
    
    -- create sequnce
    CREATE SEQUENCE IF NOT EXISTS public.{table_name}_ogc_fid_seq
        INCREMENT 1
        START 1
        MINVALUE 1
        MAXVALUE 9223372036854775807
        CACHE 1;
    """

    grant_sequnce_sql = f"""
    
    -- grant sequnce
    ALTER TABLE IF EXISTS public.{table_name}_ogc_fid_seq OWNER to postgres;
    GRANT ALL ON TABLE public.{table_name}_ogc_fid_seq TO postgres WITH GRANT OPTION;
    """

    sql = ""

    if is_grant_socl_reader:
        grant_table_sql += f"GRANT SELECT ON TABLE public.{table_name} TO socl_reader;"
        grant_sequnce_sql += (
            f"GRANT SELECT ON SEQUENCE public.{table_name} TO socl_reader;"
        )

    if is_add_ogc_fid:
        sql += create_sequnce_sql
        sql += grant_sequnce_sql

    sql += create_table_sql
    sql += grant_table_sql

    if is_add_mtime:
        sql += create_mtime_trigger_sql

    return sql


def generate_sql_to_delete_db_table(table_name, is_add_mtime=True, is_add_ogc_fid=True):
    """
    Generate SQL to delete a database table.

    Args:
        table_name (str): The name of the table.
        is_add_mtime (bool): Whether the table has MTIME column. Default is True.
        is_add_ogc_fid (bool): Whether the table has OGC_FID column. Default is True.

    Returns:
        str: SQL text to delete the database table.
    """
    sql = ""
    drop_table_sql = f"DROP TABLE IF EXISTS public.{table_name};"
    drop_sequnce_sql = f"\nDROP SEQUENCE IF EXISTS public.{table_name}_ogc_fid_seq;"
    drop_mtime_trigger_sql = (
        f"\nDROP TRIGGER IF EXISTS {table_name}_mtime ON public.{table_name};"
    )

    sql += drop_table_sql

    if is_add_mtime:
        sql += drop_mtime_trigger_sql

    if is_add_ogc_fid:
        sql += drop_sequnce_sql

    return sql


def _show_smaple_column_type():
    """
    {'example_column_name': 'example_column_type'}
    """
    example = {
        # base type
        "bool": "boolean",
        "finite_text": 'character varying(50) COLLATE pg_catalog."default"',
        "infinite_text": 'text COLLATE pg_catalog."default"',
        "int": "integer",
        "float": "double precision",
        "date": "date",
        "time_with_tz": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        # real example
        "gid": "bigint",
        "x": "double precision",
        "y": "double precision",
        "lng": "double precision",
        "lat": "double precision",
        "geometry": "geometry(MultiPolygon,3826)",
        "wkb_geometry_point": "geometry(Point,4326)",
        "wkb_geometry_line": "geometry(LineStringZ,4326)",
        "city": 'character varying(10) COLLATE pg_catalog."default"',
        "name": 'text COLLATE pg_catalog."default"',
        "dist": 'character varying(10) COLLATE pg_catalog."default"',
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "height": "double precision",
        "enable_year": "double precision",
    }

    return example


if __name__ == "__main__":
    # input
    IS_HISTRORY_TABLE = True

    TANME = "heal_hospital"
    COLUMN_MAP = {
        "data_time": "timestamp with time zone DEFAULT CURRENT_TIMESTAMP",
        "name": 'character varying(50) COLLATE pg_catalog."default"',
        "addr": 'text COLLATE pg_catalog."default"',
        "lng": "double precision",
        "lat": "double precision",
        "wkb_geometry": "geometry(Point,4326)"
    }

    if IS_HISTRORY_TABLE:
        TANME = [TANME, f"{TANME}_history"]

    for table in TANME:
        drop_table_sql = generate_sql_to_delete_db_table(table)
        print(drop_table_sql)

        create_table_sql = generate_sql_to_create_db_table(table, COLUMN_MAP)
        print(create_table_sql)