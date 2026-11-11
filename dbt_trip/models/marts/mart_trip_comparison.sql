with
accomod_stat as (
select
  city,
  any_value(nights) as trip_nights,
  round(avg(price_per_person_one_night), 2) as avg_accomod_per_one,
  max(price_per_person_one_night) as max_accomod_per_one,
  min(price_per_person_one_night) as min_accomod_per_one
from {{ ref('stg_accommodation') }}
group by city
),

items_stat as (
select
  city,
  round(sum(case when expense_category = 'food' then price_eur else 0 end), 2) as daily_food,
  round(sum(case when expense_category = 'nightlife' then price_eur else 0 end), 2) as daily_nightlife,
  round(sum(case when expense_category = 'transport' then price_eur else 0 end), 2) as daily_transport
from {{ ref('stg_prices') }}
group by city
),

final_mart as (
  select
    a.city,
    a.avg_accomod_per_one,
    i.daily_food,
    i.daily_nightlife,
    i.daily_transport,
    round(i.daily_food + i.daily_transport + i.daily_nightlife, 2) as total_daily_spending_eur,
    round(a.avg_accomod_per_one * a.trip_nights, 2) as accomod_allnights,
    round((i.daily_food + i.daily_transport + i.daily_nightlife) * a.trip_nights, 2) as total_item_spending,
    round(
      (a.avg_accomod_per_one * a.trip_nights) +
      ((i.daily_food + i.daily_transport + i.daily_nightlife) * a.trip_nights),
      2
    ) as total_budget_per_person
  from accomod_stat a
  join items_stat i on a.city = i.city
)

select *
from final_mart