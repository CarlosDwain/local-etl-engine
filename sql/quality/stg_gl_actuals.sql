SELECT count(*)
FROM stg_gl_actuals
WHERE document_number IS NULL OR line_number IS NULL
