DELETE FROM component_charts WHERE index = 'business_district_directory';

INSERT INTO component_charts (index, color, types, unit)
VALUES ('business_district_directory', array['#9b6817'], array['DistrictChart', 'ColumnChart'], '位');

SELECT * FROM component_charts ORDER BY index ASC;