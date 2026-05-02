-- Register the static health dysentery cases map component.
--
-- Required static frontend files:
--   Taipei-City-Dashboard-FE/public/mapData/health_dysentery_cases.geojson
--   Taipei-City-Dashboard-FE/public/mapData/health_dysentery_cases_taipei.geojson
--
-- The script is idempotent and can be safely rerun.

SET client_encoding = 'UTF8';

DO $$
DECLARE
    component_id integer;
    metrotaipei_map_id integer;
    taipei_map_id integer;
    dashboard_id integer;
BEGIN
    INSERT INTO public.components ("index", name)
    VALUES ('health_dysentery_cases', '痢疾病例分布')
    ON CONFLICT ("index") DO UPDATE
    SET name = EXCLUDED.name
    RETURNING id INTO component_id;

    INSERT INTO public.component_charts ("index", color, "types", unit)
    VALUES (
        'health_dysentery_cases',
        ARRAY['#E35D6A', '#3BA5C6']::varchar[],
        ARRAY['MapLegend']::varchar[],
        '區'
    )
    ON CONFLICT ("index") DO UPDATE
    SET
        color = EXCLUDED.color,
        "types" = EXCLUDED."types",
        unit = EXCLUDED.unit;

    SELECT id
    INTO metrotaipei_map_id
    FROM public.component_maps
    WHERE "index" = 'health_dysentery_cases'
    ORDER BY id
    LIMIT 1;

    IF metrotaipei_map_id IS NULL THEN
        INSERT INTO public.component_maps (
            "index",
            title,
            type,
            source,
            size,
            icon,
            paint,
            property
        )
        VALUES (
            'health_dysentery_cases',
            '雙北痢疾病例',
            'fill',
            'geojson',
            NULL,
            NULL,
            $json${
                "fill-color": [
                    "case",
                    ["==", ["get", "above_average"], true],
                    "#E35D6A",
                    "#3BA5C6"
                ],
                "fill-opacity": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    10,
                    0.45,
                    14,
                    0.62,
                    18,
                    0.74
                ],
                "fill-outline-color": "#FFFFFF"
            }$json$::json,
            $json$[
                {"key":"district","name":"行政區"},
                {"key":"city","name":"城市"},
                {"key":"year","name":"年度"},
                {"key":"amoebic_dysentery","name":"阿米巴性痢疾"},
                {"key":"bacillary_dysentery","name":"桿菌性痢疾"},
                {"key":"total_cases","name":"總病例數"},
                {"key":"average_cases","name":"平均病例數"},
                {"key":"above_average","name":"高於平均"}
            ]$json$::json
        )
        RETURNING id INTO metrotaipei_map_id;
    ELSE
        UPDATE public.component_maps
        SET
            title = '雙北痢疾病例',
            type = 'fill',
            source = 'geojson',
            size = NULL,
            icon = NULL,
            paint = $json${
                "fill-color": [
                    "case",
                    ["==", ["get", "above_average"], true],
                    "#E35D6A",
                    "#3BA5C6"
                ],
                "fill-opacity": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    10,
                    0.45,
                    14,
                    0.62,
                    18,
                    0.74
                ],
                "fill-outline-color": "#FFFFFF"
            }$json$::json,
            property = $json$[
                {"key":"district","name":"行政區"},
                {"key":"city","name":"城市"},
                {"key":"year","name":"年度"},
                {"key":"amoebic_dysentery","name":"阿米巴性痢疾"},
                {"key":"bacillary_dysentery","name":"桿菌性痢疾"},
                {"key":"total_cases","name":"總病例數"},
                {"key":"average_cases","name":"平均病例數"},
                {"key":"above_average","name":"高於平均"}
            ]$json$::json
        WHERE id = metrotaipei_map_id;
    END IF;

    SELECT id
    INTO taipei_map_id
    FROM public.component_maps
    WHERE "index" = 'health_dysentery_cases_taipei'
    ORDER BY id
    LIMIT 1;

    IF taipei_map_id IS NULL THEN
        INSERT INTO public.component_maps (
            "index",
            title,
            type,
            source,
            size,
            icon,
            paint,
            property
        )
        VALUES (
            'health_dysentery_cases_taipei',
            '臺北痢疾病例',
            'fill',
            'geojson',
            NULL,
            NULL,
            $json${
                "fill-color": [
                    "case",
                    ["==", ["get", "above_average"], true],
                    "#E35D6A",
                    "#3BA5C6"
                ],
                "fill-opacity": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    10,
                    0.45,
                    14,
                    0.62,
                    18,
                    0.74
                ],
                "fill-outline-color": "#FFFFFF"
            }$json$::json,
            $json$[
                {"key":"district","name":"行政區"},
                {"key":"city","name":"城市"},
                {"key":"year","name":"年度"},
                {"key":"amoebic_dysentery","name":"阿米巴性痢疾"},
                {"key":"bacillary_dysentery","name":"桿菌性痢疾"},
                {"key":"total_cases","name":"總病例數"},
                {"key":"average_cases","name":"平均病例數"},
                {"key":"above_average","name":"高於平均"}
            ]$json$::json
        )
        RETURNING id INTO taipei_map_id;
    ELSE
        UPDATE public.component_maps
        SET
            title = '臺北痢疾病例',
            type = 'fill',
            source = 'geojson',
            size = NULL,
            icon = NULL,
            paint = $json${
                "fill-color": [
                    "case",
                    ["==", ["get", "above_average"], true],
                    "#E35D6A",
                    "#3BA5C6"
                ],
                "fill-opacity": [
                    "interpolate",
                    ["linear"],
                    ["zoom"],
                    10,
                    0.45,
                    14,
                    0.62,
                    18,
                    0.74
                ],
                "fill-outline-color": "#FFFFFF"
            }$json$::json,
            property = $json$[
                {"key":"district","name":"行政區"},
                {"key":"city","name":"城市"},
                {"key":"year","name":"年度"},
                {"key":"amoebic_dysentery","name":"阿米巴性痢疾"},
                {"key":"bacillary_dysentery","name":"桿菌性痢疾"},
                {"key":"total_cases","name":"總病例數"},
                {"key":"average_cases","name":"平均病例數"},
                {"key":"above_average","name":"高於平均"}
            ]$json$::json
        WHERE id = taipei_map_id;
    END IF;

    DELETE FROM public.query_charts
    WHERE "index" = 'health_dysentery_cases'
      AND city IN ('metrotaipei', 'taipei');

    INSERT INTO public.query_charts (
        "index",
        history_config,
        map_config_ids,
        map_filter,
        time_from,
        time_to,
        update_freq,
        update_freq_unit,
        source,
        short_desc,
        long_desc,
        use_case,
        links,
        contributors,
        created_at,
        updated_at,
        query_type,
        query_chart,
        query_history,
        city
    )
    VALUES
    (
        'health_dysentery_cases',
        NULL,
        ARRAY[metrotaipei_map_id]::integer[],
        NULL,
        'static',
        NULL,
        0,
        'static',
        '靜態 GeoJSON',
        '雙北各行政區 113 年阿米巴性痢疾與桿菌性痢疾病例分布。',
        '以雙北行政區面圖呈現 113 年痢疾病例數，紅色代表該行政區病例數高於平均值，藍色代表未高於平均值。',
        '協助快速掌握痢疾病例在雙北行政區的空間分布與相對高低。',
        ARRAY[]::text[],
        ARRAY[]::text[],
        NOW(),
        NOW(),
        'map_legend',
        $chart_sql$
            SELECT '高於平均'::text AS name, 'fill'::text AS type, ''::text AS icon, 17::float AS value
            UNION ALL
            SELECT '未高於平均'::text AS name, 'fill'::text AS type, ''::text AS icon, 24::float AS value
        $chart_sql$,
        NULL,
        'metrotaipei'
    ),
    (
        'health_dysentery_cases',
        NULL,
        ARRAY[taipei_map_id]::integer[],
        NULL,
        'static',
        NULL,
        0,
        'static',
        '靜態 GeoJSON',
        '臺北市各行政區 113 年阿米巴性痢疾與桿菌性痢疾病例分布。',
        '以臺北市行政區面圖呈現 113 年痢疾病例數，紅色代表該行政區病例數高於平均值，藍色代表未高於平均值。',
        '協助快速掌握痢疾病例在臺北市行政區的空間分布與相對高低。',
        ARRAY[]::text[],
        ARRAY[]::text[],
        NOW(),
        NOW(),
        'map_legend',
        $chart_sql$
            SELECT '高於平均'::text AS name, 'fill'::text AS type, ''::text AS icon, 7::float AS value
            UNION ALL
            SELECT '未高於平均'::text AS name, 'fill'::text AS type, ''::text AS icon, 5::float AS value
        $chart_sql$,
        NULL,
        'taipei'
    );

    INSERT INTO public.dashboards (
        "index",
        name,
        components,
        icon,
        updated_at,
        created_at
    )
    VALUES (
        'health_dysentery_cases_map',
        '痢疾病例分布',
        ARRAY[component_id]::integer[],
        'local_hospital',
        NOW(),
        NOW()
    )
    ON CONFLICT ("index") DO UPDATE
    SET
        name = EXCLUDED.name,
        components = EXCLUDED.components,
        icon = EXCLUDED.icon,
        updated_at = NOW()
    RETURNING id INTO dashboard_id;

    INSERT INTO public.dashboard_groups (dashboard_id, group_id)
    SELECT dashboard_id, id
    FROM public.groups
    WHERE name IN ('taipei', 'metrotaipei')
    ON CONFLICT DO NOTHING;

    UPDATE public.dashboards
    SET
        components = CASE
            WHEN components IS NULL THEN ARRAY[component_id]::integer[]
            WHEN component_id = ANY(components) THEN components
            ELSE array_append(components, component_id)
        END,
        updated_at = NOW()
    WHERE "index" = 'map-layers-metrotaipei';

    UPDATE public.dashboards
    SET
        components = CASE
            WHEN components IS NULL THEN ARRAY[component_id]::integer[]
            WHEN component_id = ANY(components) THEN components
            ELSE array_append(components, component_id)
        END,
        updated_at = NOW()
    WHERE "index" = 'map-layers-taipei';

    PERFORM setval('public.components_id_seq', GREATEST((SELECT MAX(id) FROM public.components), 1), true);
    PERFORM setval('public.component_maps_id_seq', GREATEST((SELECT MAX(id) FROM public.component_maps), 1), true);
    PERFORM setval('public.dashboards_id_seq', GREATEST((SELECT MAX(id) FROM public.dashboards), 1), true);
END $$;
