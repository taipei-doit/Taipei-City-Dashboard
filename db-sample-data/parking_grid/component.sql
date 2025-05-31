DELETE FROM components WHERE index = 'parking_grid';

INSERT INTO components (index, name) VALUES ('parking_grid', '停車格');

SELECT * FROM public.components ORDER BY id ASC;