DELETE FROM components WHERE index = 'business_district_directory';

INSERT INTO components (id, index, name) VALUES (40, 'business_district_directory', '理事長聯絡網絡');

SELECT * FROM public.components ORDER BY id ASC;