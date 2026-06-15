from sqlalchemy.sql import text as sa_text

from utils.generate_sql_to_create_DB_table import generate_sql_to_create_db_table


def _quote_identifier(identifier):
    return '"' + str(identifier).replace('"', '""') + '"'


def ensure_ready_table(engine, table_name, col_map, column_renames=None):
    sql = generate_sql_to_create_db_table(table_name, col_map)
    with engine.connect() as conn:
        if column_renames:
            existing_columns = {
                row[0]
                for row in conn.execute(
                    sa_text(
                        """
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name = :table_name
                        """
                    ),
                    {"table_name": table_name},
                )
            }
            for old_name, new_name in column_renames.items():
                if old_name in existing_columns and new_name not in existing_columns:
                    conn.execute(
                        sa_text(
                            "ALTER TABLE public.{table_name} "
                            "RENAME COLUMN {old_name} TO {new_name}".format(
                                table_name=_quote_identifier(table_name),
                                old_name=_quote_identifier(old_name),
                                new_name=_quote_identifier(new_name),
                            )
                        ).execution_options(autocommit=True)
                    )
        conn.execute(sa_text(sql).execution_options(autocommit=True))
