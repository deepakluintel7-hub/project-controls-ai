# Synthetic 1,800 MW CCGT – Level 3 Schedule Dataset

A fully synthetic EPC schedule for a combined-cycle power plant, built for testing
schedule analytics, EVM and AI forecasting tools. **No real project, client, vendor,
location or commercial data is used.** Regenerate at any time with:

```bash
python scripts/generate_synthetic_ccgt_schedule.py
```

## Plant configuration

Two 2-2-1 power blocks (≈900 MW each): 4 gas turbines (GT11, GT12, GT21, GT22),
4 HRSGs, 2 steam turbine generators (STG10, STG20). Common balance of plant:
400 kV GIS switchyard, fuel gas station, water treatment/demin plant, cooling water
intake/outfall, central control building & DCS, auxiliary buildings, fire protection.
Block 2 is staggered 90 days behind Block 1.

## Time and cost conventions

| Item | Convention |
|---|---|
| Time | Calendar days from NTP (Day 0). Month = 30 days. |
| Cost | `budget_pct_of_bac` — % of Budget at Completion. Sums to exactly 100%. |
| Cost loading | Linear across each activity's duration (simplification; real procurement is usually milestone-paid). |
| PM / site supervision | Level-of-effort hammock spanning NTP → completion; excluded from critical path. |
| Block CODs | Contractual finish-no-later-than constraints at baseline dates, so slippage shows as negative float. |

## Files (`data/`)

**activities.csv** — activity register: `activity_id`, `wbs`, `activity_name`, `discipline`,
`phase`, `duration_days`, `activity_type` (Task / Milestone / LOE), `budget_pct_of_bac`.

**relationships.csv** — logic: `predecessor`, `successor`, `rel_type` (FS / SS / FF), `lag_days`
(negative = lead).

**baseline_cpm.csv** — baseline CPM: `early_start`, `early_finish`, `late_start`, `late_finish`,
`total_float`, `critical` (TF ≤ 0), `near_critical` (0 < TF ≤ 30 days).

**progress_update.csv** — status at data date **Day 300 (~Month 10)**: baseline and forecast dates,
`planned_pct_complete`, `actual_pct_complete`, `pv_pct_of_bac`, `ev_pct_of_bac`,
`ac_pct_of_bac`, `finish_variance_days`, `forecast_total_float`.

**monthly_s_curve.csv** — cumulative `pv_cum_pct`, `ev_cum_pct`, `ac_cum_pct` (to data date)
and `forecast_cum_pct` by month.

## Built-in delay & cost scenario (what the data should reveal)

| Driver | Effect | Lesson for analysis |
|---|---|---|
| Permits approved 45 days late | Delays site enabling and civil start | Absorbed by float — no COD impact |
| GT21 manufacturing +75 days | Large equipment delay | Float consumed from 110 → 35 days; **equipment delay ≠ project delay** |
| HRSG22 pressure parts +35 days | On the critical path | **Block 2 COD slips 35 days** (negative float −35) |
| 400 kV GIS manufacturing +30 days | Backfeed later | Absorbed by float |
| Civil productivity −20% | Civil durations ×1.2 | Drives SPI and civil cost variance |
| Unit cost overruns by discipline | Civil 12%, Mgmt 6%, Mech 4%, Elec 3%, I&C 2% | Drives CPI below 1.0 |

**Headline results at Day 300:** PV 26.1% · EV 25.0% · AC 26.5% · **SPI 0.96 · CPI 0.94** ·
Block 1 COD on time · Block 2 COD +35 days.

Change the `slip`, `civil_productivity` and `cost_factor` values in the script to create new
scenarios for testing forecasting models.
