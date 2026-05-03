-- dashboardmanager：為 component_charts 增加 stacked（縱向長條是否堆疊）
-- TRUE：維持既有堆疊行為；FALSE：並列分組（適用單位不同之多系列）
ALTER TABLE public.component_charts
  ADD COLUMN IF NOT EXISTS stacked boolean NOT NULL DEFAULT TRUE;
