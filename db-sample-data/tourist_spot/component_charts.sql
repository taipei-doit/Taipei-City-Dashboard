DELETE FROM component_charts WHERE index = 'tourist_spot';

INSERT INTO component_charts (index, color, types, unit)
VALUES ('tourist_spot', array['#abcd00'], array['DistrictChart', 'BarChart'], '人次');

SELECT * FROM component_charts ORDER BY index ASC;