-- depends_on: stg_gl_actuals
SELECT
    document_number,
    line_number,
    posting_date,
    gl_account,
    amount_usd,
    cost_center,
    _source_file, _sheet, _row_number, _file_hash, _ingested_at, period
FROM stg_gl_actuals
