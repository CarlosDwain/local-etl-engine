-- depends_on: raw.gl_actuals
SELECT
    trim(document_number)                  AS document_number,
    TRY_CAST(line_number AS INTEGER)        AS line_number,
    TRY_CAST(posting_date AS DATE)          AS posting_date,
    trim(gl_account)                        AS gl_account,
    TRY_CAST(replace(amount_usd, ',', '') AS DECIMAL(18, 2)) AS amount_usd,
    trim(cost_center)                       AS cost_center,
    _source_file, _sheet, _row_number, _file_hash, _ingested_at, period
FROM raw_gl_actuals
