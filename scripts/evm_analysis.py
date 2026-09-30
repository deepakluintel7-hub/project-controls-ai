"""
EVM Analysis for a cost-loaded schedule update
==============================================

Reads data/progress_update.csv and data/monthly_s_curve.csv and produces:

  reports/evm_by_discipline.csv   - PV / EV / AC, variances and indices per discipline
  reports/schedule_drivers.csv    - activities driving the forecast delay
  reports/evm_summary.md          - one-page management summary
  reports/s_curve.png             - PV / EV / AC / forecast S-curve

Metrics: SV, CV, SPI, CPI, EAC (three methods), ETC, VAC, TCPI, and Earned Schedule
(ES, SPI(t), IEAC(t)) - which, unlike SPI, stays reliable late in a project.

Costs in the dataset are % of BAC. Pass --bac to express results in currency:
    python scripts/evm_analysis.py
    python scripts/evm_analysis.py --bac 1250000000 --currency USD
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA, REPORTS = ROOT / "data", ROOT / "reports"
DAYS_PER_MONTH = 30


# ----------------------------------------------------------------------------------------
# Core EVM calculations
# ----------------------------------------------------------------------------------------

def safe_div(a, b):
    return a / b if b else float("nan")


def evm_metrics(pv: float, ev: float, ac: float, bac: float) -> dict:
    spi, cpi = safe_div(ev, pv), safe_div(ev, ac)
    eac_cpi = safe_div(bac, cpi)                       # remaining work at current cost efficiency
    eac_budget = ac + (bac - ev)                       # remaining work at budget rate
    eac_composite = ac + safe_div(bac - ev, cpi * spi)  # cost and schedule pressure combined
    return dict(
        PV=pv, EV=ev, AC=ac, SV=ev - pv, CV=ev - ac, SPI=spi, CPI=cpi,
        EAC_CPI=eac_cpi, EAC_budget_rate=eac_budget, EAC_CPIxSPI=eac_composite,
        ETC=eac_cpi - ac, VAC=bac - eac_cpi,
        TCPI_BAC=safe_div(bac - ev, bac - ac),         # efficiency needed to finish on budget
        TCPI_EAC=safe_div(bac - ev, eac_cpi - ac),
    )


def earned_schedule(curve: pd.DataFrame, ev_now: float, data_date_day: int,
                    planned_duration_days: int) -> dict:
    """ES = time at which the baseline PV curve reached today's EV (linear interpolation)."""
    es_day = float(np.interp(ev_now, curve.pv_cum_pct, curve.day))
    spi_t = safe_div(es_day, data_date_day)
    return dict(ES_day=es_day, AT_day=data_date_day, SV_t_days=es_day - data_date_day,
                SPI_t=spi_t, IEAC_t_days=safe_div(planned_duration_days, spi_t))


# ----------------------------------------------------------------------------------------
# Analysis
# ----------------------------------------------------------------------------------------

def by_discipline(prog: pd.DataFrame, scale: float) -> pd.DataFrame:
    g = prog.groupby("discipline").agg(
        BAC=("budget_pct_of_bac", "sum"), PV=("pv_pct_of_bac", "sum"),
        EV=("ev_pct_of_bac", "sum"), AC=("ac_pct_of_bac", "sum"))
    g = g[g.BAC > 0] * scale
    g["SV"], g["CV"] = g.EV - g.PV, g.EV - g.AC
    g["SPI"] = (g.EV / g.PV).where(g.PV > 0)
    g["CPI"] = (g.EV / g.AC).where(g.AC > 0)
    g["EAC"] = (g.BAC / g.CPI).where(g.CPI > 0, g.BAC)
    g["VAC"] = g.BAC - g.EAC
    return g.sort_values("CV").round(3)


def schedule_drivers(prog: pd.DataFrame) -> pd.DataFrame:
    """Activities that are late AND have lost float - the ones management must act on."""
    d = prog[(prog.finish_variance_days > 0) & (prog.activity_type != "LOE")].copy()
    d["float_lost_days"] = d.total_float - d.forecast_total_float
    d["status"] = np.select(
        [d.forecast_total_float < 0, d.forecast_total_float <= 30],
        ["DRIVING DELAY (negative float)", "At risk (<= 30 d float)"], "Absorbed by float")
    cols = ["activity_id", "activity_name", "discipline", "early_finish", "forecast_finish",
            "finish_variance_days", "total_float", "forecast_total_float",
            "float_lost_days", "status"]
    order = {"DRIVING DELAY (negative float)": 0, "At risk (<= 30 d float)": 1, "Absorbed by float": 2}
    return (d[cols].assign(_o=d.status.map(order))
            .sort_values(["_o", "forecast_total_float", "finish_variance_days"],
                         ascending=[True, True, False])
            .drop(columns="_o"))


def status_flag(index: float) -> str:
    if np.isnan(index):
        return "n/a"
    return "GREEN" if index >= 0.98 else "AMBER" if index >= 0.93 else "RED"


# ----------------------------------------------------------------------------------------
# Outputs
# ----------------------------------------------------------------------------------------

def plot_s_curve(curve: pd.DataFrame, data_date_day: int, path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5.5))
    m = curve.day / DAYS_PER_MONTH
    ax.plot(m, curve.pv_cum_pct, label="Planned Value (baseline)", color="#1f4e79", lw=2)
    ax.plot(m, curve.forecast_cum_pct, label="Forecast", color="#7f7f7f", lw=1.5, ls="--")
    hist = curve[curve.ev_cum_pct.notna()]
    ax.plot(hist.day / DAYS_PER_MONTH, hist.ev_cum_pct, label="Earned Value", color="#2e7d32", lw=2.5)
    ax.plot(hist.day / DAYS_PER_MONTH, hist.ac_cum_pct, label="Actual Cost", color="#c62828", lw=2.5)
    ax.axvline(data_date_day / DAYS_PER_MONTH, color="black", lw=1, ls=":")
    ax.text(data_date_day / DAYS_PER_MONTH + 0.3, 5, "Data date", fontsize=9)
    ax.set(xlabel="Project month", ylabel="Cumulative % of BAC", ylim=(0, 102),
           title="Cost-loaded S-curve - PV / EV / AC")
    ax.grid(alpha=0.3); ax.legend(loc="upper left")
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def fmt(v, unit):
    return f"{v:,.2f}%" if unit == "%" else f"{unit} {v:,.0f}"


def write_summary(path, total, es, disc, drivers, milestones, unit, data_date_day):
    driving = drivers[drivers.status.str.startswith("DRIVING")]
    absorbed = drivers[drivers.status == "Absorbed by float"]
    worst_cost = disc.index[0]
    lines = [
        "# EVM Status Report",
        "",
        f"**Data date:** Day {data_date_day} (Month {data_date_day / DAYS_PER_MONTH:.0f}) · "
        f"**Units:** {'% of BAC' if unit == '%' else unit}",
        "",
        "## Headline",
        "",
        "| Metric | Value | Status |",
        "|---|---|---|",
        f"| SPI | {total['SPI']:.2f} | {status_flag(total['SPI'])} |",
        f"| CPI | {total['CPI']:.2f} | {status_flag(total['CPI'])} |",
        f"| SPI(t) - earned schedule | {es['SPI_t']:.2f} | {status_flag(es['SPI_t'])} |",
        f"| Schedule variance (time) | {es['SV_t_days']:+.0f} days | |",
        f"| EAC (BAC / CPI) | {fmt(total['EAC_CPI'], unit)} | |",
        f"| VAC | {fmt(total['VAC'], unit)} | |",
        f"| TCPI to achieve BAC | {total['TCPI_BAC']:.2f} | "
        f"{'Very difficult' if total['TCPI_BAC'] > 1.10 else 'Challenging' if total['TCPI_BAC'] > 1.05 else 'Achievable'} |",
        "",
        "## Key milestones",
        "",
        "| Milestone | Baseline (day) | Forecast (day) | Variance |",
        "|---|---|---|---|",
    ]
    for r in milestones.itertuples():
        lines.append(f"| {r.activity_name} | {r.early_finish} | {r.forecast_finish} | "
                     f"{r.finish_variance_days:+d} days |")
    lines += [
        "",
        "## What is driving the delay",
        "",
        f"{len(driving)} activities are on a negative-float path and are driving milestone slippage. "
        f"{len(absorbed)} late activities are currently absorbed by float - they need monitoring, "
        "not recovery spend.",
        "",
        "| Activity | Late by | Float now | Status |",
        "|---|---|---|---|",
    ]
    for r in pd.concat([driving.head(6), absorbed.head(3)]).itertuples():
        lines.append(f"| {r.activity_id} {r.activity_name} | {r.finish_variance_days} d | "
                     f"{r.forecast_total_float} d | {r.status} |")
    lines += [
        "",
        "## Cost performance by discipline",
        "",
        "| Discipline | CPI | SPI | CV | EAC |",
        "|---|---|---|---|---|",
    ]
    for d, r in disc.iterrows():
        cpi = "not started" if pd.isna(r.CPI) else f"{r.CPI:.2f}"
        spi = "not started" if pd.isna(r.SPI) else f"{r.SPI:.2f}"
        lines.append(f"| {d} | {cpi} | {spi} | {fmt(r.CV, unit)} | {fmt(r.EAC, unit)} |")
    lines += [
        "",
        "## Management attention",
        "",
        f"1. **Schedule:** focus recovery on the negative-float path "
        f"(first driver: {driving.iloc[0].activity_id} {driving.iloc[0].activity_name}). "
        "Large delays elsewhere are absorbed by float - verify, don't spend on them."
        if len(driving) else "1. **Schedule:** no activity is on a negative-float path.",
        f"2. **Cost:** {worst_cost} has the weakest CPI ({disc.loc[worst_cost, 'CPI']:.2f}). "
        "Decompose its variance into price, quantity and productivity before corrective action.",
        f"3. **Forecast:** EAC range {fmt(min(total['EAC_budget_rate'], total['EAC_CPI']), unit)} "
        f"to {fmt(total['EAC_CPIxSPI'], unit)} depending on whether current efficiency persists.",
        "",
        "_Generated by scripts/evm_analysis.py_",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# ----------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="EVM analysis of a cost-loaded schedule update")
    ap.add_argument("--bac", type=float, default=None, help="Budget at completion in currency")
    ap.add_argument("--currency", default="USD")
    args = ap.parse_args()

    prog = pd.read_csv(DATA / "progress_update.csv")
    curve = pd.read_csv(DATA / "monthly_s_curve.csv")
    REPORTS.mkdir(exist_ok=True)

    scale = args.bac / 100 if args.bac else 1.0
    unit = args.currency if args.bac else "%"
    bac = 100 * scale
    data_date = int(prog.data_date_day.iloc[0])
    planned_duration = int(prog.early_finish.max())

    total = evm_metrics(prog.pv_pct_of_bac.sum() * scale, prog.ev_pct_of_bac.sum() * scale,
                        prog.ac_pct_of_bac.sum() * scale, bac)
    es = earned_schedule(curve, prog.ev_pct_of_bac.sum(), data_date, planned_duration)
    disc = by_discipline(prog, scale)
    drivers = schedule_drivers(prog)
    milestones = prog[prog.activity_type == "Milestone"].query("early_finish > 0")

    disc.to_csv(REPORTS / "evm_by_discipline.csv")
    drivers.to_csv(REPORTS / "schedule_drivers.csv", index=False)
    write_summary(REPORTS / "evm_summary.md", total, es, disc, drivers, milestones, unit, data_date)
    plot_s_curve(curve, data_date, REPORTS / "s_curve.png")

    print(f"Data date day {data_date} | SPI {total['SPI']:.2f} | CPI {total['CPI']:.2f} | "
          f"SPI(t) {es['SPI_t']:.2f} | EAC {fmt(total['EAC_CPI'], unit)} | TCPI {total['TCPI_BAC']:.2f}")
    print(f"Reports written to {REPORTS}")


if __name__ == "__main__":
    main()
