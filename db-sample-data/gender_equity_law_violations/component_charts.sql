DELETE FROM component_charts
WHERE index = 'gender_equity_law_violations';

INSERT INTO component_charts (index, color, types, unit)
VALUES ('gender_equity_law_violations', array['#67baca', '#abcd00'], array['TimelineSeparateChart', 'TimelineStackedChart', 'ColumnLineChart'], '件');

SELECT * FROM public.component_charts
ORDER BY index ASC;