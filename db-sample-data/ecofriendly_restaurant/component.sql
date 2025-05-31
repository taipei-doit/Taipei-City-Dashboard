DELETE FROM components WHERE index = 'ecofriendly_restaurant';

INSERT INTO components (index, name) VALUES ('ecofriendly_restaurant', '環保餐廳');

SELECT * FROM public.components ORDER BY id ASC;