WITH source_data AS (
  SELECT *
  FROM {{source ('raw', 'numbeo_prices')}}
),
cleaned AS (
  SELECT
    city,
    item_name,
    price_eur,
    _loaded_at,
    CASE
      WHEN REGEXP_CONTAINS(item_name, r'(?i)beer|wine|cider|vodka|cocktail|pub|bar')
        THEN 'nightlife'
      WHEN REGEXP_CONTAINS(item_name, r'(?i)meal|cappuccino|coffee|restaurant|lunch|dinner|burger|mcdonald')
        THEN 'food'
      WHEN REGEXP_CONTAINS(item_name, r'(?i)taxi|ticket|bus|metro|train|transport|pass')
        THEN 'transport'
      ELSE 'other'
    END AS expense_category
  FROM source_data
)

SELECT *
FROM cleaned