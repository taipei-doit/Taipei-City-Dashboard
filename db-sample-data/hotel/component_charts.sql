DELETE FROM component_charts WHERE index = 'hotel';

INSERT INTO component_charts (index, color, types, unit)
VALUES ('hotel', array['#C49797'], array['MapLegend'], '間');

SELECT * FROM component_charts ORDER BY index ASC;