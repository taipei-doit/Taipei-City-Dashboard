BEGIN;

-- 組件 AI 摘要。DAG proj_city_dashboard/component_ai_summary 產製後寫入，
-- 由 BE 讀出供前端顯示。schema 對齊 SIT 現況（SIT 是手動建立、未進版控，
-- 這份 migration 補上該 DDL 以便 prod 及後續環境可重現）。
--
-- 兩個目標 DB 都是 dashboardmanager（Airflow connection: dashboard-postgre）。

-- 1) 讓 query_charts 能標記哪些組件要產 AI 摘要。
--    DAG 以 `WHERE enable_ai_summary IS TRUE` 篩選，預設 false 代表新組件不會
--    自動開啟，需由管理端明確指定。
ALTER TABLE public.query_charts
    ADD COLUMN IF NOT EXISTS enable_ai_summary boolean NOT NULL DEFAULT false;

-- 2) 摘要結果表。
--    type 目前有 chart（圖表摘要）與 map（地圖圖層摘要）兩種，
--    (index, city) 對應 query_charts 的同名欄位。
--    刻意不設 (index, city, type) 唯一鍵：DAG 用純 INSERT 逐次附加，
--    保留歷次摘要供比對，讀取端取最新一筆即可（與 SIT 現況一致）。
CREATE TABLE IF NOT EXISTS public.component_ai_summary (
    id         bigserial PRIMARY KEY,
    index      varchar     NOT NULL,
    city       text        NOT NULL,
    type       text        NOT NULL,
    result     text        NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL
);

-- 讀取端固定以 (index, city, type) 撈某組件的最新摘要，補一個複合索引。
CREATE INDEX IF NOT EXISTS component_ai_summary_lookup_idx
    ON public.component_ai_summary (index, city, type, created_at DESC);

ALTER TABLE IF EXISTS public.component_ai_summary OWNER TO airflow;

COMMIT;
