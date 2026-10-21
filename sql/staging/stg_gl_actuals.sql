-- depends_on: raw.gl_actuals
-- TODO(step 3): TRY_CAST typed columns, trim text, dedupe on business key, keep lineage columns.
SELECT
    document_number,
    TRY_CAST(line_number AS INTEGER)       AS line_number,
    TRY_CAST(posting_date AS DATE)         AS posting_date,
    gl_account,
    TRY_CAST(amount_usd AS DECIMAL(18, 2)) AS amount_usd,
    cost_center,
    _source_file, _sheet, _row_number, _file_hash, _ingested_at, period
FROM raw_gl_actuals
