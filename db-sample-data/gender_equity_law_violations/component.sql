DELETE FROM components
WHERE index = 'gender_equity_law_violations';

INSERT INTO components (id, index, name)
VALUES (88, 'gender_equity_law_violations', '性平法違法件數');

SELECT * FROM public.components
ORDER BY id ASC;