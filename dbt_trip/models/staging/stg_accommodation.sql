with source_data as (
  select *
  from {{ source('raw', 'accommodation') }}
),
cleaned as (
  select
      city,
      title AS listing_title,
      subtitle,
      rating,
      guests,
      nights,
      checkin,
      checkout,
      price_eur AS total_price_eur,
      round(price_eur / nullif(nights, 0), 2) as price_per_night,
      round(price_eur / (nullif(nights, 0)* nullif(guests, 0)), 2) as price_per_person_one_night,
      _loaded_at
      from source_data
      where price_eur is not null
        and price_eur >=50
)

select *
from cleaned


