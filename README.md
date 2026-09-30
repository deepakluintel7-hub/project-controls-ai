# Project Controls AI

**AI-assisted schedule and cost analytics for EPC power projects**

This repository explores how data analytics and AI can support traditional project controls:
critical path analysis, earned value management (EVM), delay analysis and recovery
scenario planning. It is built by a project controls practitioner, for practitioners.

---

## What's inside

| Folder | Contents |
|---|---|
| `scripts/` | Python tools. Currently: a synthetic schedule generator with its own CPM engine. |
| `data/` | A fully synthetic 1,800 MW CCGT Level 3 schedule (139 activities, 223 logic links), cost-loaded as % of BAC, with a Month-10 progress update. |
| `docs/` | Data dictionary and methodology notes. |

## The sample dataset

A two-block 2-2-1 combined-cycle plant (4 GT, 4 HRSG, 2 STG) plus switchyard, fuel gas,
water treatment, cooling water and DCS. The Day-300 status update contains a deliberate
delay story for analysis tools to uncover:

- A 75-day gas turbine manufacturing delay that is **mostly absorbed by float**
- A 35-day HRSG delay **on the critical path** that moves Block 2 COD by 35 days
- Reduced civil productivity and discipline-level cost overruns
- Result at the data date: **SPI 0.96, CPI 0.94**

All data is synthetic. No real project, client, vendor or commercial information is used.
See [`docs/synthetic_dataset.md`](docs/synthetic_dataset.md) for the full data dictionary.

## Quick start

```bash
pip install pandas
python scripts/generate_synthetic_ccgt_schedule.py
```

The script rebuilds every CSV in `data/`. Edit the `slip`, `civil_productivity` and
`cost_factor` values to create new delay and cost scenarios.

## Roadmap

- [x] Synthetic cost-loaded CCGT schedule with CPM (FS/SS/FF, lags, contractual milestones)
- [ ] Cost variance decomposition (price / quantity / timing)
- [x] EVM dashboard: SPI, CPI, EAC and TCPI trends
- [ ] Critical and near-critical path change detection between updates
- [ ] Recovery scenario generator (optimistic / most likely / pessimistic) using an LLM
- [ ] Monte Carlo schedule risk analysis (QSRA)

## About

**Deepak Luintel, PMP®** — Project planning and controls professional with 16+ years in
power generation, energy and heavy-crane EPC projects across China, the UAE, Oman and
Bahrain. Primavera P6, EVM, forensic delay analysis and QSRA. Focused on applying AI to
project controls.

[LinkedIn](https://www.linkedin.com/in/deepak-luintel/)

## License

MIT
