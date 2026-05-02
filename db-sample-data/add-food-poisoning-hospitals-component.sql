-- Add/update the metrotaipei food poisoning hospital capacity component.
--
-- Required static frontend file:
--   Taipei-City-Dashboard-FE/public/mapData/food_poisoning_hospitals_metrotaipei.geojson
--
-- The script is idempotent and can be safely rerun.

SET client_encoding = 'UTF8';

DO $$
DECLARE
    component_id bigint;
    map_id bigint;
BEGIN
    INSERT INTO public.components ("index", name)
    VALUES ('food_poisoning_hospitals', '食物中毒收治醫院量能')
    ON CONFLICT ("index") DO UPDATE
    SET name = EXCLUDED.name
    RETURNING id INTO component_id;

    INSERT INTO public.component_charts ("index", color, "types", unit)
    VALUES (
        'food_poisoning_hospitals',
        ARRAY['#9CA3AF', '#FFFFFF', '#9CA3AF']::varchar[],
        ARRAY['TextUnitChart']::varchar[],
        NULL
    )
    ON CONFLICT ("index") DO UPDATE
    SET
        color = EXCLUDED.color,
        "types" = EXCLUDED."types",
        unit = EXCLUDED.unit;

    SELECT id
    INTO map_id
    FROM public.component_maps
    WHERE "index" = 'food_poisoning_hospitals_metrotaipei'
    ORDER BY id
    LIMIT 1;

    IF map_id IS NULL THEN
        SELECT id
        INTO map_id
        FROM public.component_maps
        WHERE "index" = 'food_poining_hospitals_metrotaipei'
        ORDER BY id
        LIMIT 1;

        IF map_id IS NOT NULL THEN
            UPDATE public.component_maps
            SET "index" = 'food_poisoning_hospitals_metrotaipei'
            WHERE id = map_id;
        END IF;
    END IF;

    IF map_id IS NULL THEN
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
            'food_poisoning_hospitals_metrotaipei',
            '食物中毒收治醫院',
            'symbol',
            'geojson',
            NULL,
            'cross_bold',
            '{}'::json,
            $json$[
                {"key":"縣市","name":"縣市"},
                {"key":"行政區","name":"行政區"},
                {"key":"醫院名稱","name":"醫院名稱"},
                {"key":"地址","name":"地址"},
                {"key":"電話","name":"電話"},
                {"key":"補齊醫事機構代碼","name":"醫事機構代碼"},
                {"key":"食物中毒_急診觀察床","name":"急診觀察床"},
                {"key":"食物中毒_急性一般病床","name":"急性一般病床"},
                {"key":"食物中毒_核心病床","name":"核心病床"},
                {"key":"食物中毒_加護病床","name":"加護病床"},
                {"key":"食物中毒_隔離病床","name":"隔離病床"},
                {"key":"食物中毒_相關病床總數","name":"相關病床總數"}
            ]$json$::json
        )
        RETURNING id INTO map_id;
    ELSE
        UPDATE public.component_maps
        SET
            title = '食物中毒收治醫院',
            type = 'symbol',
            source = 'geojson',
            size = NULL,
            icon = 'cross_bold',
            paint = '{}'::json,
            property = $json$[
                {"key":"縣市","name":"縣市"},
                {"key":"行政區","name":"行政區"},
                {"key":"醫院名稱","name":"醫院名稱"},
                {"key":"地址","name":"地址"},
                {"key":"電話","name":"電話"},
                {"key":"補齊醫事機構代碼","name":"醫事機構代碼"},
                {"key":"食物中毒_急診觀察床","name":"急診觀察床"},
                {"key":"食物中毒_急性一般病床","name":"急性一般病床"},
                {"key":"食物中毒_核心病床","name":"核心病床"},
                {"key":"食物中毒_加護病床","name":"加護病床"},
                {"key":"食物中毒_隔離病床","name":"隔離病床"},
                {"key":"食物中毒_相關病床總數","name":"相關病床總數"}
            ]$json$::json
        WHERE id = map_id;
    END IF;

    DELETE FROM public.query_charts
    WHERE "index" = 'food_poisoning_hospitals'
      AND city = 'metrotaipei';

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
    VALUES (
        'food_poisoning_hospitals',
        NULL,
        ARRAY[map_id]::integer[],
        '{}'::json,
        'static',
        NULL,
        0,
        NULL,
        '臺北市與新北市食物中毒收治醫院病床資料',
        '臺北市與新北市食物中毒收治醫院病床資料 | 固定資料',
        '呈現臺北市與新北市可支援食物中毒收治的醫院點位，包含醫院名稱、行政區、地址、電話、醫事機構代碼，以及急診觀察床、急性一般病床、核心病床、加護病床、隔離病床與相關病床總數等量能資訊。',
        '協助食安事件或大量病患應變時，快速盤點雙北地區可用醫療院所與相關病床資源。',
        ARRAY[]::text[],
        ARRAY['doit', 'ntpc']::text[],
        NOW(),
        NOW(),
        'three_d',
        $chart_sql$
            SELECT '總計'::text AS x_axis, '收治醫院'::text AS y_axis, '家'::text AS icon, 66::int AS data
            UNION ALL
            SELECT '總計'::text AS x_axis, '相關病床總數'::text AS y_axis, '床'::text AS icon, 16372::int AS data
            UNION ALL
            SELECT '總計'::text AS x_axis, '急診觀察床'::text AS y_axis, '床'::text AS icon, 649::int AS data
            UNION ALL
            SELECT '總計'::text AS x_axis, '加護與隔離病床'::text AS y_axis, '床'::text AS icon, 1604::int AS data
        $chart_sql$,
        NULL,
        'metrotaipei'
    );

    UPDATE public.dashboards
    SET
        components = CASE
            WHEN components IS NULL THEN ARRAY[component_id]::integer[]
            WHEN component_id::integer = ANY(components) THEN components
            ELSE array_append(components, component_id::integer)
        END,
        updated_at = NOW()
    WHERE "index" = 'map-layers-metrotaipei';
END $$;
