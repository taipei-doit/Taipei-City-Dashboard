DELETE FROM components WHERE index = 'hotel';

INSERT INTO components (index, name) VALUES ('hotel', '旅館');

SELECT * FROM public.components ORDER BY id ASC;