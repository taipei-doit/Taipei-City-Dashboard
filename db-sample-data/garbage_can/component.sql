DELETE FROM components WHERE index = 'garbage_can';

INSERT INTO components (id, index, name) VALUES (89, 'garbage_can', '垃圾桶分佈');

SELECT * FROM public.components ORDER BY id ASC;