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

## My Profile

# Hi, I'm Deepak Luintel 👋

### PMP® | Project Controls & Planning Professional | AI-Enabled Scheduling Advocate

I have 16+ years of international experience in **power generation, energy, and heavy crane industries**, delivering complex EPC, commissioning, and industrial projects across **China, UAE, Oman, and Bahrain**. I'm now applying **AI, machine learning, and automation** to modernize how projects are planned, tendered, monitored, and controlled.

---

## 🎯 What I Do

**Project Planning & Scheduling**
- WBS development, baseline creation, and critical path analysis
- Schedule updating, schedule recovery, and forensic delay analysis
- Quantitative Schedule Risk Analysis (QSRA)
- Tools: Primavera P6, Microsoft Project

**Cost Control & Earned Value Management**
- Project estimation and cost baselining
- EVM (CPI, SPI, EAC, ETC) and cost forecasting
- Change management and variance analysis

**Tendering & Bidding**
- Tender planning and bid schedule development
- Bid document review and clarification management
- Cost estimation support and resource-loaded bid programs
- Risk and assumptions identification at bid stage

**Document Reconciliation & Contract Controls**
- Reconciliation of tender documents, addenda, and revisions
- Scope, BOQ, and specification cross-checking
- Requirements and scope traceability
- Claims support and change order documentation

**Project Reporting & Governance**
- Executive dashboards and progress reporting
- Stakeholder and requirements management
- Monitoring, control, and performance reviews

---

## 🤖 AI x Project Controls (What I'm Building)

I believe the future of project management is the convergence of **AI, data analytics, and digital project controls**. My focus areas:

- 📄 **Automated tender/bid document comparison and reconciliation** (detecting changes, gaps, and conflicts between revisions)
- 📊 **Automated progress and executive reporting**
- 📈 **ML-based schedule forecasting and delay prediction**
- ⚠️ **AI-assisted risk identification** from historical project data
- 👷 **Resource planning optimization**
- 🔁 **Intelligent automation of P6 / MS Project data workflows**

---

## 🛠️ Tech & Tools

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-4479A1?style=flat&logo=postgresql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=flat&logo=powerbi&logoColor=black)
![Excel](https://img.shields.io/badge/Excel-217346?style=flat&logo=microsoftexcel&logoColor=white)

**Project Controls:** Primavera P6 • Microsoft Project • EVM • QSRA • Forensic Delay Analysis
**Learning:** Machine Learning • LLMs & Prompt Engineering • Data Analytics • Automation

---

## 📂 Projects & Repositories

- `schedule-analytics` – Python scripts for analyzing P6/XER schedule data *(in progress)*
- `evm-dashboard` – Earned value calculations and visualization *(in progress)*
- `tender-doc-reconciliation` – Compare tender revisions and flag changes using AI *(in progress)*
- `ai-project-reporting` – Automated progress report generation *(planned)*

---

## 🌍 Languages

English • Mandarin Chinese • Nepali • Hindi • Urdu

---

## 📫 Let's Connect

- 💼 LinkedIn: [LinkedIn](https://www.linkedin.com/in/deepak-luintel/)
- 📧 Email: luintel.deepak@outlook.com

> *"Bridging traditional project management with next-generation AI to deliver more predictable, efficient, and successful projects."*
##
