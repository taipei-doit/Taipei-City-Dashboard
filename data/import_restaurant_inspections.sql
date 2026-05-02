BEGIN;

DROP TABLE IF EXISTS public.restaurant_inspection_locations CASCADE;
DROP TABLE IF EXISTS public.restaurant_inspections_raw CASCADE;

CREATE TABLE public.restaurant_inspections_raw (
    sample_name text,
    inspection_address text,
    inspection_result text,
    noncompliance_reason text,
    source_year text,
    source_city text,
    lon text,
    lat text,
    restaurant_name text
);

\copy public.restaurant_inspections_raw(sample_name, inspection_address, inspection_result, noncompliance_reason, source_year, source_city, lon, lat, restaurant_name) FROM '/tmp/final_merged_2_geo_named.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8');

CREATE TABLE public.restaurant_inspection_locations AS
WITH cleaned AS (
    SELECT
        NULLIF(BTRIM(sample_name), '') AS sample_name,
        NULLIF(BTRIM(inspection_address), '') AS inspection_address,
        COALESCE(NULLIF(BTRIM(inspection_result), ''), '未知') AS inspection_result,
        NULLIF(BTRIM(noncompliance_reason), '') AS noncompliance_reason,
        NULLIF(BTRIM(source_year), '') AS source_year,
        NULLIF(BTRIM(source_city), '') AS source_city,
        lon::double precision AS lon,
        lat::double precision AS lat,
        NULLIF(BTRIM(restaurant_name), '') AS restaurant_name
    FROM public.restaurant_inspections_raw
    WHERE
        lon ~ '^-?[0-9]+(\.[0-9]+)?$'
        AND lat ~ '^-?[0-9]+(\.[0-9]+)?$'
        AND NULLIF(BTRIM(restaurant_name), '') IS NOT NULL
),
grouped AS (
    SELECT
        restaurant_name,
        inspection_address,
        source_city,
        lon,
        lat,
        COUNT(*)::integer AS total_inspections,
        COUNT(*) FILTER (WHERE inspection_result = '不合格')::integer AS failed_inspections,
        STRING_AGG(DISTINCT source_year, '、' ORDER BY source_year) AS source_years,
        STRING_AGG(DISTINCT sample_name, '、' ORDER BY sample_name) AS sample_names,
        STRING_AGG(DISTINCT noncompliance_reason, '；' ORDER BY noncompliance_reason)
            FILTER (WHERE inspection_result = '不合格' AND noncompliance_reason IS NOT NULL)
            AS noncompliance_reasons
    FROM cleaned
    GROUP BY restaurant_name, inspection_address, source_city, lon, lat
)
SELECT
    ROW_NUMBER() OVER (ORDER BY restaurant_name, inspection_address, lon, lat)::integer AS ogc_fid,
    restaurant_name,
    inspection_address,
    source_city,
    lon,
    lat,
    total_inspections,
    failed_inspections,
    CASE WHEN failed_inspections > 0 THEN '不合格' ELSE '合格' END AS inspection_status,
    source_years,
    sample_names,
    noncompliance_reasons,
    ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geometry(Point, 4326) AS wkb_geometry,
    NOW()::timestamp with time zone AS _ctime,
    NOW()::timestamp with time zone AS _mtime
FROM grouped;

ALTER TABLE public.restaurant_inspection_locations
    ADD CONSTRAINT restaurant_inspection_locations_pkey PRIMARY KEY (ogc_fid);

CREATE INDEX restaurant_inspection_locations_geom_idx
    ON public.restaurant_inspection_locations
    USING gist (wkb_geometry);

CREATE INDEX restaurant_inspection_locations_status_idx
    ON public.restaurant_inspection_locations (inspection_status);

COMMIT;

COPY (
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', COALESCE(json_agg(ST_AsGeoJSON(t.*)::json ORDER BY ogc_fid), '[]'::json)
    )
    FROM (
        SELECT
            ogc_fid,
            restaurant_name,
            inspection_address,
            source_city,
            lon,
            lat,
            total_inspections,
            failed_inspections,
            inspection_status,
            source_years,
            sample_names,
            noncompliance_reasons,
            wkb_geometry
        FROM public.restaurant_inspection_locations
    ) AS t
) TO '/tmp/restaurant_inspections_all.geojson' WITH (FORMAT text, ENCODING 'UTF8');

COPY (
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', COALESCE(json_agg(ST_AsGeoJSON(t.*)::json ORDER BY ogc_fid), '[]'::json)
    )
    FROM (
        SELECT
            ogc_fid,
            restaurant_name,
            inspection_address,
            source_city,
            lon,
            lat,
            total_inspections,
            failed_inspections,
            inspection_status,
            source_years,
            sample_names,
            noncompliance_reasons,
            wkb_geometry
        FROM public.restaurant_inspection_locations
        WHERE inspection_status = '不合格'
    ) AS t
) TO '/tmp/restaurant_inspections_failed.geojson' WITH (FORMAT text, ENCODING 'UTF8');
