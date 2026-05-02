-- Create tables for traceability_inspection and cas_product DAGs
-- Run before first DAG execution (save_dataframe_to_postgresql uses TRUNCATE)

CREATE TABLE IF NOT EXISTS public.traceability_inspection (
    sampling_location   TEXT,
    inspect_result      TEXT,
    raw_data            JSONB,
    data_time           TEXT
);

CREATE TABLE IF NOT EXISTS public.cas_product (
    material_name   TEXT,
    raw_data        JSONB,
    data_time       TEXT
);
