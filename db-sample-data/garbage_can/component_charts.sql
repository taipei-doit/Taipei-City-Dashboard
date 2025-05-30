DELETE FROM component_charts WHERE index = 'garbage_can';

INSERT INTO component_charts (index, color, types, unit)
VALUES ('garbage_can', array['#abcd00'], array['DistrictChart', 'ColumnChart'], '個');

SELECT * FROM component_charts ORDER BY index ASC;