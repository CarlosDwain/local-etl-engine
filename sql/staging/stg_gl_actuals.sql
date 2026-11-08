-- depends_on: raw.gl_actuals
WITH valid AS (
    SELECT
        *,
        TRY_CAST(line_number AS INTEGER) AS cast_line_number,
        TRY_CAST(posting_date AS DATE) AS cast_posting_date,
        TRY_CAST(replace(amount_usd, ',', '') AS DECIMAL(18, 2)) AS cast_amount_usd
    FROM raw_gl_actuals
    WHERE period = $period
      AND NULLIF(trim(document_number), '') IS NOT NULL
      AND TRY_CAST(line_number AS INTEGER) IS NOT NULL
      AND TRY_CAST(posting_date AS DATE) IS NOT NULL
      AND NULLIF(trim(gl_account), '') IS NOT NULL
      AND TRY_CAST(replace(amount_usd, ',', '') AS DECIMAL(18, 2)) IS NOT NULL
), ranked AS (
    SELECT *, row_number() OVER (
        PARTITION BY document_number, cast_line_number ORDER BY _row_number
    ) AS key_occurrence
    FROM valid
)
SELECT
    trim(document_number)                  AS document_number,
    cast_line_number                        AS line_number,
    cast_posting_date                       AS posting_date,
    trim(gl_account)                        AS gl_account,
    cast_amount_usd                         AS amount_usd,
    trim(cost_center)                       AS cost_center,
    _source_file, _sheet, _row_number, _file_hash, _ingested_at, period
FROM ranked
WHERE key_occurrence = 1
