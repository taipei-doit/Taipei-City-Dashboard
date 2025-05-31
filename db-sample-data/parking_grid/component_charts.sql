DELETE FROM component_charts WHERE index = 'parking_grid';

INSERT INTO component_charts (index, color, types, unit)
VALUES ('parking_grid', array['#090974', '#033E6B', '#0C60A4', '#4F2981', '#7373D8', '#66A2D2'], array['ColumnChart', 'PolarAreaChart'], '格');

SELECT * FROM component_charts ORDER BY index ASC;