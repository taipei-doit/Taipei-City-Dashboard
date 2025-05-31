DELETE FROM components WHERE index = 'parking_grid';

INSERT INTO components (id, index, name) VALUES (3, 'parking_grid', '停車格');

SELECT * FROM public.components ORDER BY id ASC;