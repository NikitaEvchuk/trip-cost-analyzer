# Student Holiday Trip Cost Analyzer — Warsaw vs. Utrecht

End-to-end analytics pipeline that answers a practical question: **which city is cheaper (and better value) for a New Year's trip with friends?**

It goes beyond accommodation and models daily spending: nightlife (pint, shots, club entry), street food & coffee, public transport and student-friendly activities (ice rinks, museums).

## Stack
`Excel` → `Python (pandas)` → `BigQuery` → `dbt` → `Power BI`

```
Open APIs / Excel ──> Python extract ──> BigQuery raw ──> dbt (staging → intermediate → marts) ──> Power BI
```

## Data sources (open only)
| Domain | Source |
|---|---|
| POIs (bars, clubs, food, ice rinks, museums) | OpenStreetMap Overpass API |
| FX rates | Frankfurter (ECB), NBP API |
| Price levels | Eurostat `prc_ppp_ind` |
| Daily prices, transport, accommodation offers | Manually collected Excel sheets (with source URLs) |

## Interactive parameters
Group size · trip dates / nights · display currency (EUR default) · spending profile (budget / medium / party) · accommodation type.

## Project structure
```
extract/      Python extract & load scripts
data/manual/  Excel inputs
data/raw/     downloaded files (git-ignored)
dbt_trip/     dbt project
notebooks/    exploratory analysis
powerbi/      Power BI report
```

## Status
🚧 Work in progress — see roadmap below.

- [x] Phase 0 — setup & source validation
- [ ] Phase 1 — manual data collection (Excel)
- [ ] Phase 2 — Python extract
- [ ] Phase 3 — MVP (pandas + Power BI on CSV)
- [ ] Phase 4 — BigQuery
- [ ] Phase 5 — dbt models & tests
- [ ] Phase 6 — Power BI dashboard
- [ ] Phase 7 — findings & recommendation
