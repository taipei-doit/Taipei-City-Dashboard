DELETE FROM component_charts WHERE index = 'ecofriendly_restaurant';

INSERT INTO component_charts (index, color, types, unit)
VALUES ('ecofriendly_restaurant', array['#C49797'], array['MapLegend'], '間');

SELECT * FROM component_charts ORDER BY index ASC;