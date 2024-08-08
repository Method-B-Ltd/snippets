DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT
            c.relname AS sequence_name,
            a.attname AS column_name,
            t.relname AS table_name
        FROM
            pg_class c
            JOIN pg_depend d ON d.objid = c.oid
            JOIN pg_class t ON t.oid = d.refobjid
            JOIN pg_attribute a ON a.attnum = d.refobjsubid AND a.attrelid = t.oid
        WHERE
            c.relkind = 'S'
            AND t.relkind = 'r'
            AND c.relname LIKE '%_id_seq'
    LOOP
        EXECUTE format('SELECT setval(''%I'', (SELECT max(%I) FROM %I))', r.sequence_name, r.column_name, r.table_name);
    END LOOP;
END $$;