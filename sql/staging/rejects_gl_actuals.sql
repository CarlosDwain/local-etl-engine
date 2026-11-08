-- depends_on: raw.gl_actuals
WITH invalid AS (
    SELECT
        CAST(document_number AS VARCHAR) AS document_number,
        _source_file, _sheet, _row_number, period,
        CASE
            WHEN NULLIF(trim(document_number), '') IS NULL THEN 'document_number: required value is null'
            WHEN TRY_CAST(line_number AS INTEGER) IS NULL THEN 'line_number: value is not an integer'
            WHEN TRY_CAST(posting_date AS DATE) IS NULL THEN 'posting_date: value is not a date'
            WHEN NULLIF(trim(gl_account), '') IS NULL THEN 'gl_account: required value is null'
            WHEN TRY_CAST(replace(amount_usd, ',', '') AS DECIMAL(18, 2)) IS NULL THEN
                CASE WHEN starts_with(trim(amount_usd), '(') THEN 'amount_usd: negative amount' ELSE 'amount_usd: value is not a decimal' END
            ELSE 'unknown: row validation failed'
        END AS reason
    FROM raw_gl_actuals
    WHERE period = $period
      AND (
           NULLIF(trim(document_number), '') IS NULL
       OR TRY_CAST(line_number AS INTEGER) IS NULL
       OR TRY_CAST(posting_date AS DATE) IS NULL
       OR NULLIF(trim(gl_account), '') IS NULL
       OR TRY_CAST(replace(amount_usd, ',', '') AS DECIMAL(18, 2)) IS NULL
      )
), valid AS (
    SELECT *, row_number() OVER (
        PARTITION BY document_number, TRY_CAST(line_number AS INTEGER)
        ORDER BY _row_number
    ) AS key_occurrence
    FROM raw_gl_actuals
    WHERE period = $period
      AND NULLIF(trim(document_number), '') IS NOT NULL
      AND TRY_CAST(line_number AS INTEGER) IS NOT NULL
      AND TRY_CAST(posting_date AS DATE) IS NOT NULL
      AND NULLIF(trim(gl_account), '') IS NOT NULL
      AND TRY_CAST(replace(amount_usd, ',', '') AS DECIMAL(18, 2)) IS NOT NULL
), duplicate AS (
    SELECT CAST(document_number AS VARCHAR) AS document_number,
           _source_file, _sheet, _row_number, period,
           'document_number,line_number: duplicate business key' AS reason
    FROM valid
    WHERE key_occurrence > 1
)
SELECT * FROM invalid
UNION ALL
SELECT * FROM duplicate
