-- ============================================================
-- Minimal schema for eco_cup component registration
-- Run this before db_setup.sql if tables don't exist
-- ============================================================

CREATE TABLE IF NOT EXISTS public.components (
    id SERIAL PRIMARY KEY,
    index VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.component_charts (
    index VARCHAR(255) PRIMARY KEY,
    color VARCHAR[],
    types VARCHAR[],
    unit VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS public.component_maps (
    id SERIAL PRIMARY KEY,
    index VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    size VARCHAR(255),
    icon VARCHAR(255),
    paint JSON,
    property JSON
);

CREATE TABLE IF NOT EXISTS public.query_charts (
    index VARCHAR(255) NOT NULL,
    history_config JSON,
    map_config_ids INTEGER[],
    map_filter JSON,
    time_from VARCHAR(255),
    time_to VARCHAR(255),
    update_freq INTEGER,
    update_freq_unit VARCHAR(255),
    source VARCHAR(255),
    short_desc TEXT,
    long_desc TEXT,
    use_case TEXT,
    links TEXT[],
    contributors TEXT[],
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    query_type VARCHAR(255),
    query_chart TEXT,
    query_history TEXT,
    city VARCHAR(255) NOT NULL,
    PRIMARY KEY (index, city)
);
