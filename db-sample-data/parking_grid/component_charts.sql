DELETE FROM component_charts WHERE index = 'parking_grid';

INSERT INTO component_charts (index, color, types, unit)
VALUES ('parking_grid', array['#ff3f66'], array['MapLegend'], '間');

SELECT * FROM component_charts ORDER BY index ASC;