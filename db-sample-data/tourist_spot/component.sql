DELETE FROM components WHERE index = 'tourist_spot';

INSERT INTO components (id, index, name) VALUES (30, 'tourist_spot', '商圈景點遊客');

SELECT * FROM public.components ORDER BY id ASC;