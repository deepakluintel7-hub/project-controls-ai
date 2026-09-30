"""
Synthetic 1,800 MW CCGT (Level 3) schedule generator
=====================================================

Builds a fully synthetic, non-confidential EPC schedule for a 1,800 MW
combined-cycle power plant (two 2-2-1 power blocks: 4 GT, 4 HRSG, 2 STG)
and produces:

  data/activities.csv        - activity register, WBS, durations, cost weight (% of BAC)
  data/relationships.csv     - logic (FS / SS / FF with lags)
  data/baseline_cpm.csv      - CPM results: ES/EF/LS/LF, total float, critical flags
  data/progress_update.csv   - status at the data date: PV / EV / AC per activity (% of BAC)
  data/monthly_s_curve.csv   - cumulative PV / EV / AC / forecast by project month

No real project, client, vendor or location data is used. Durations are
calendar days measured from NTP (Day 0). All costs are % of total budget (BAC).

Run:  python scripts/generate_synthetic_ccgt_schedule.py
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data"
DATA_DATE = 300          # status date, days after NTP (~ month 10)
NEAR_CRITICAL_FLOAT = 30  # days
HAMMOCKS = {"PM-0001"}    # level-of-effort activities (not schedule drivers)
CONTRACT_MILESTONES = ["MS-1100", "MS-2100"]  # block CODs are contractual (finish-no-later-than baseline)

# --------------------------------------------------------------------------------------
# 1. Activity + logic definition
# --------------------------------------------------------------------------------------
acts: list[dict] = []
rels: list[dict] = []


def A(aid, wbs, name, disc, phase, dur, weight=0.0):
    """Register an activity. weight = relative cost units (normalised to % later)."""
    acts.append(dict(activity_id=aid, wbs=wbs, activity_name=name, discipline=disc,
                     phase=phase, duration_days=dur, cost_weight=weight,
                     activity_type="Milestone" if dur == 0 else "Task"))
    return aid


def L(pred, succ, rtype="FS", lag=0):
    rels.append(dict(predecessor=pred, successor=succ, rel_type=rtype, lag_days=lag))


# ---- Project milestones & management ------------------------------------------------
A("MS-0001", "1.0 Milestones", "Notice to Proceed (NTP)", "Management", "Milestone", 0)
A("PM-0001", "1.1 Project Management", "Project management & site supervision (LOE)",
  "Management", "Management", 0, 3.0)   # LOE / hammock: duration set from NTP to COD after CPM
acts[-1]["activity_type"] = "LOE"
L("MS-0001", "PM-0001")

# ---- Engineering (common) -----------------------------------------------------------
A("ENG-0001", "2.1 Engineering - General", "Topographic survey & geotechnical investigation", "Civil", "Engineering", 60, 0.25)
A("ENG-0002", "2.1 Engineering - General", "Basic design, plot plan & heat balance", "Process", "Engineering", 90, 0.60)
A("ENG-0003", "2.1 Engineering - General", "Environmental & construction permits", "Management", "Engineering", 180, 0.15)
A("ENG-0004", "2.2 Engineering - Civil", "Civil & structural detail design", "Civil", "Engineering", 150, 0.80)
A("ENG-0005", "2.2 Engineering - Civil", "Civil IFC drawings - power block foundations", "Civil", "Engineering", 45, 0.20)
A("ENG-0006", "2.3 Engineering - Mechanical", "Mechanical & piping detail design", "Mechanical", "Engineering", 210, 1.10)
A("ENG-0007", "2.3 Engineering - Mechanical", "Piping isometrics IFC", "Mechanical", "Engineering", 60, 0.30)
A("ENG-0008", "2.4 Engineering - Electrical & I&C", "Electrical & I&C detail design", "Electrical", "Engineering", 210, 0.90)
A("ENG-0009", "2.4 Engineering - Electrical & I&C", "Cable schedules & I/O list IFC", "Electrical", "Engineering", 60, 0.20)
L("MS-0001", "ENG-0001"); L("MS-0001", "ENG-0002", "SS", 15); L("MS-0001", "ENG-0003")
L("ENG-0001", "ENG-0004"); L("ENG-0002", "ENG-0004", "SS", 45)
L("ENG-0004", "ENG-0005", "SS", 90)
L("ENG-0002", "ENG-0006"); L("ENG-0006", "ENG-0007", "SS", 150)
L("ENG-0002", "ENG-0008", "SS", 30); L("ENG-0008", "ENG-0009", "SS", 150)

# ---- Site enabling ------------------------------------------------------------------
A("CON-0001", "4.1 Construction - Enabling", "Site mobilisation & temporary facilities", "Civil", "Construction", 60, 0.50)
A("CON-0002", "4.1 Construction - Enabling", "Site grading, drainage & roads", "Civil", "Construction", 90, 0.90)
L("ENG-0003", "CON-0001", "SS", 60); L("CON-0001", "CON-0002", "SS", 30); L("ENG-0001", "CON-0002")

# ---- Balance of plant (common systems) ----------------------------------------------
# 400 kV switchyard (needed for backfeed before GT first fire)
A("PRC-0901", "3.9 Procurement - Switchyard", "400 kV GIS - PO award", "Electrical", "Procurement", 30, 0.05)
A("PRC-0902", "3.9 Procurement - Switchyard", "400 kV GIS - manufacture & FAT", "Electrical", "Procurement", 300, 2.40)
A("PRC-0903", "3.9 Procurement - Switchyard", "400 kV GIS - shipment to site", "Electrical", "Procurement", 45, 0.15)
A("CON-0901", "4.9 Construction - Switchyard", "Switchyard civil works & GIS building", "Civil", "Construction", 150, 0.90)
A("CON-0902", "4.9 Construction - Switchyard", "GIS erection & HV testing", "Electrical", "Construction", 90, 0.60)
A("COM-0901", "5.9 Commissioning - Switchyard", "Switchyard energisation / backfeed power", "Electrical", "Commissioning", 15, 0.10)
L("ENG-0008", "PRC-0901", "SS", 60); L("PRC-0901", "PRC-0902"); L("PRC-0902", "PRC-0903")
L("CON-0002", "CON-0901", "SS", 45); L("ENG-0005", "CON-0901")
L("CON-0901", "CON-0902"); L("PRC-0903", "CON-0902"); L("CON-0902", "COM-0901")

# Fuel gas receiving station
A("PRC-0911", "3.9 Procurement - BOP", "Fuel gas skid & metering - supply", "Mechanical", "Procurement", 270, 0.90)
A("CON-0911", "4.9 Construction - BOP", "Fuel gas station installation & tie-in", "Mechanical", "Construction", 120, 0.40)
A("COM-0911", "5.9 Commissioning - BOP", "Fuel gas system purge & gas-in", "Mechanical", "Commissioning", 20, 0.05)
L("ENG-0006", "PRC-0911", "SS", 90); L("PRC-0911", "CON-0911"); L("CON-0002", "CON-0911")
L("CON-0911", "COM-0911")

# Water treatment plant (demin water needed for hydrotest / steam blow)
A("PRC-0921", "3.9 Procurement - BOP", "Water treatment & demin plant - supply", "Mechanical", "Procurement", 240, 1.10)
A("CON-0921", "4.9 Construction - BOP", "Water treatment plant construction", "Mechanical", "Construction", 150, 0.70)
A("COM-0921", "5.9 Commissioning - BOP", "Water treatment plant commissioning", "Mechanical", "Commissioning", 30, 0.10)
L("ENG-0006", "PRC-0921", "SS", 60); L("PRC-0921", "CON-0921", "SS", 180); L("CON-0002", "CON-0921")
L("CON-0921", "COM-0921")

# Cooling water system (needed before steam turbine roll)
A("CON-0931", "4.9 Construction - BOP", "Cooling water intake & outfall civil works", "Civil", "Construction", 270, 2.20)
A("PRC-0931", "3.9 Procurement - BOP", "Cooling water pumps & screens - supply", "Mechanical", "Procurement", 300, 1.20)
A("CON-0932", "4.9 Construction - BOP", "Cooling water pumps & piping installation", "Mechanical", "Construction", 120, 0.90)
A("COM-0931", "5.9 Commissioning - BOP", "Cooling water system commissioning", "Mechanical", "Commissioning", 30, 0.10)
L("ENG-0005", "CON-0931"); L("ENG-0006", "PRC-0931", "SS", 60)
L("CON-0931", "CON-0932", "FS", -60); L("PRC-0931", "CON-0932"); L("CON-0932", "COM-0931")

# Control building & DCS
A("CON-0941", "4.9 Construction - BOP", "Central control building (civil & MEP)", "Civil", "Construction", 210, 1.00)
A("PRC-0941", "3.9 Procurement - BOP", "DCS & plant control system - supply & FAT", "I&C", "Procurement", 270, 1.60)
A("CON-0942", "4.9 Construction - BOP", "DCS installation & power-up", "I&C", "Construction", 60, 0.30)
A("COM-0941", "5.9 Commissioning - BOP", "DCS loop checks & software validation", "I&C", "Commissioning", 60, 0.15)
L("ENG-0005", "CON-0941"); L("ENG-0008", "PRC-0941", "SS", 90)
L("CON-0941", "CON-0942"); L("PRC-0941", "CON-0942"); L("CON-0942", "COM-0941")

# Auxiliary buildings & fire protection (typically off the critical path)
A("CON-0951", "4.9 Construction - BOP", "Admin, workshop & warehouse buildings", "Civil", "Construction", 240, 1.20)
A("CON-0952", "4.9 Construction - BOP", "Fire protection system installation", "Mechanical", "Construction", 150, 0.60)
A("COM-0951", "5.9 Commissioning - BOP", "Fire protection system commissioning", "Mechanical", "Commissioning", 20, 0.05)
L("CON-0002", "CON-0951", "FS", 60); L("CON-0952", "COM-0951")

# ---- Power blocks (2 x 2-2-1) --------------------------------------------------------
BLOCK_OFFSET = {1: 0, 2: 90}  # block 2 staggered 90 days
cod_ms = []

for b in (1, 2):
    off = BLOCK_OFFSET[b]
    B = f"B{b}"
    gts = [f"GT{b}1", f"GT{b}2"]

    # Block-level procurement awards
    A(f"PRC-{b}001", f"3.{b} Procurement - Block {b}", f"Block {b} - GT package PO award", "Mechanical", "Procurement", 30, 0.05)
    A(f"PRC-{b}002", f"3.{b} Procurement - Block {b}", f"Block {b} - HRSG package PO award", "Mechanical", "Procurement", 30, 0.05)
    A(f"PRC-{b}003", f"3.{b} Procurement - Block {b}", f"Block {b} - STG package PO award", "Mechanical", "Procurement", 30, 0.05)
    L("ENG-0002", f"PRC-{b}001", "FS", off); L("ENG-0002", f"PRC-{b}002", "FS", off + 15)
    L("ENG-0002", f"PRC-{b}003", "FS", off + 30)

    # Steam turbine generator (one per block)
    A(f"PRC-{b}031", f"3.{b} Procurement - Block {b}", f"STG{b}0 - manufacture & FAT", "Mechanical", "Procurement", 420, 5.20)
    A(f"PRC-{b}032", f"3.{b} Procurement - Block {b}", f"STG{b}0 - shipment to site", "Mechanical", "Procurement", 45, 0.25)
    A(f"PRC-{b}033", f"3.{b} Procurement - Block {b}", f"STG{b}0 GSU transformer - supply", "Electrical", "Procurement", 330, 0.70)
    L(f"PRC-{b}003", f"PRC-{b}031"); L(f"PRC-{b}031", f"PRC-{b}032")
    L(f"PRC-{b}003", f"PRC-{b}033", "FS", 30)

    A(f"CON-{b}031", f"4.{b} Construction - Block {b}", f"STG{b}0 - turbine hall & TG pedestal", "Civil", "Construction", 180, 1.40)
    A(f"CON-{b}032", f"4.{b} Construction - Block {b}", f"STG{b}0 - erection & alignment", "Mechanical", "Construction", 150, 0.90)
    A(f"CON-{b}033", f"4.{b} Construction - Block {b}", f"STG{b}0 - condenser & auxiliaries", "Mechanical", "Construction", 120, 0.60)
    A(f"CON-{b}034", f"4.{b} Construction - Block {b}", f"STG{b}0 GSU transformer install & test", "Electrical", "Construction", 45, 0.15)
    L("ENG-0005", f"CON-{b}031", "FS", off); L(f"CON-{b}031", f"CON-{b}032")
    L(f"PRC-{b}032", f"CON-{b}032"); L(f"CON-{b}032", f"CON-{b}033", "SS", 60)
    L(f"PRC-{b}033", f"CON-{b}034"); L(f"CON-{b}031", f"CON-{b}034")

    # Block-level BOP piping and E&I
    A(f"CON-{b}041", f"4.{b} Construction - Block {b}", f"Block {b} - BOP piping erection", "Mechanical", "Construction", 240, 1.60)
    A(f"CON-{b}042", f"4.{b} Construction - Block {b}", f"Block {b} - cable pulling & terminations", "Electrical", "Construction", 210, 1.30)
    A(f"CON-{b}043", f"4.{b} Construction - Block {b}", f"Block {b} - instrumentation installation", "I&C", "Construction", 150, 0.60)
    L("ENG-0007", f"CON-{b}041", "FS", off); L("ENG-0009", f"CON-{b}042", "FS", off)
    L(f"CON-{b}042", f"CON-{b}043", "SS", 60)

    steam_blows = []
    for g in gts:
        n = g[-1]
        pid = f"{b}{n}"  # e.g. 11, 12, 21, 22
        H = g.replace("GT", "HRSG")

        # --- GT procurement
        A(f"PRC-{pid}11", f"3.{b} Procurement - Block {b}", f"{g} - gas turbine manufacture & FAT", "Mechanical", "Procurement", 360, 4.60)
        A(f"PRC-{pid}12", f"3.{b} Procurement - Block {b}", f"{g} - shipment & delivery to site", "Mechanical", "Procurement", 45, 0.20)
        A(f"PRC-{pid}13", f"3.{b} Procurement - Block {b}", f"{g} GSU transformer - supply", "Electrical", "Procurement", 330, 0.70)
        stagger = 0 if n == "1" else 45
        L(f"PRC-{b}001", f"PRC-{pid}11", "FS", stagger); L(f"PRC-{pid}11", f"PRC-{pid}12")
        L(f"PRC-{b}001", f"PRC-{pid}13", "FS", 30 + stagger)

        # --- HRSG procurement
        A(f"PRC-{pid}21", f"3.{b} Procurement - Block {b}", f"{H} - modules & pressure parts manufacture", "Mechanical", "Procurement", 330, 3.10)
        A(f"PRC-{pid}22", f"3.{b} Procurement - Block {b}", f"{H} - shipment (modules)", "Mechanical", "Procurement", 60, 0.35)
        L(f"PRC-{b}002", f"PRC-{pid}21", "FS", stagger); L(f"PRC-{pid}21", f"PRC-{pid}22")

        # --- GT construction
        A(f"CON-{pid}11", f"4.{b} Construction - Block {b}", f"{g} - foundation & enclosure base", "Civil", "Construction", 90, 0.70)
        A(f"CON-{pid}12", f"4.{b} Construction - Block {b}", f"{g} - set on foundation", "Mechanical", "Construction", 15, 0.10)
        A(f"CON-{pid}13", f"4.{b} Construction - Block {b}", f"{g} - erection, alignment & auxiliaries", "Mechanical", "Construction", 90, 0.60)
        A(f"CON-{pid}14", f"4.{b} Construction - Block {b}", f"{g} GSU transformer install & test", "Electrical", "Construction", 45, 0.15)
        L("ENG-0005", f"CON-{pid}11", "FS", off + stagger); L("CON-0002", f"CON-{pid}11")
        L(f"CON-{pid}11", f"CON-{pid}12"); L(f"PRC-{pid}12", f"CON-{pid}12")
        L(f"CON-{pid}12", f"CON-{pid}13")
        L(f"PRC-{pid}13", f"CON-{pid}14"); L(f"CON-{pid}11", f"CON-{pid}14")

        # --- HRSG construction
        A(f"CON-{pid}21", f"4.{b} Construction - Block {b}", f"{H} - foundation", "Civil", "Construction", 75, 0.55)
        A(f"CON-{pid}22", f"4.{b} Construction - Block {b}", f"{H} - steel structure & module erection", "Mechanical", "Construction", 180, 1.60)
        A(f"CON-{pid}23", f"4.{b} Construction - Block {b}", f"{H} - stack erection", "Mechanical", "Construction", 45, 0.30)
        A(f"CON-{pid}24", f"4.{b} Construction - Block {b}", f"{H} - hydrostatic test", "Mechanical", "Construction", 20, 0.05)
        L("ENG-0005", f"CON-{pid}21", "FS", off + stagger); L("CON-0002", f"CON-{pid}21")
        L(f"CON-{pid}21", f"CON-{pid}22"); L(f"PRC-{pid}22", f"CON-{pid}22", "SS", 0)
        L(f"PRC-{pid}21", f"CON-{pid}22", "FS", 30)  # first modules arrive ~30d after mfg ends
        L(f"CON-{pid}22", f"CON-{pid}23", "SS", 90); L(f"CON-{pid}22", f"CON-{pid}24")
        L("COM-0921", f"CON-{pid}24")

        # --- Commissioning per GT/HRSG train
        A(f"COM-{pid}11", f"5.{b} Commissioning - Block {b}", f"{g}/{H} - pre-commissioning & system checks", "Commissioning", "Commissioning", 45, 0.20)
        A(f"COM-{pid}12", f"5.{b} Commissioning - Block {b}", f"{g} - first fire & FSNL", "Commissioning", "Commissioning", 10, 0.10)
        A(f"COM-{pid}13", f"5.{b} Commissioning - Block {b}", f"{g} - first synchronisation & load tests", "Commissioning", "Commissioning", 20, 0.10)
        A(f"COM-{pid}14", f"5.{b} Commissioning - Block {b}", f"{H} - chemical cleaning & steam blow", "Commissioning", "Commissioning", 30, 0.15)
        L(f"CON-{pid}13", f"COM-{pid}11"); L(f"CON-{pid}24", f"COM-{pid}11")
        L(f"CON-{b}043", f"COM-{pid}11"); L("COM-0941", f"COM-{pid}11")
        L(f"COM-{pid}11", f"COM-{pid}12"); L("COM-0901", f"COM-{pid}11")
        L("COM-0911", f"COM-{pid}12"); L(f"CON-{pid}14", f"COM-{pid}12")
        L(f"COM-{pid}12", f"COM-{pid}13"); L(f"COM-{pid}13", f"COM-{pid}14")
        L(f"CON-{pid}23", f"COM-{pid}14"); L(f"CON-{b}041", f"COM-{pid}14")
        steam_blows.append(f"COM-{pid}14")

    # Steam turbine & block completion
    A(f"COM-{b}031", f"5.{b} Commissioning - Block {b}", f"STG{b}0 - first roll & synchronisation", "Commissioning", "Commissioning", 20, 0.15)
    A(f"COM-{b}032", f"5.{b} Commissioning - Block {b}", f"Block {b} - combined-cycle load tests & tuning", "Commissioning", "Commissioning", 30, 0.20)
    A(f"COM-{b}033", f"5.{b} Commissioning - Block {b}", f"Block {b} - performance & reliability run", "Commissioning", "Commissioning", 30, 0.20)
    A(f"MS-{b}100", "1.0 Milestones", f"Block {b} Commercial Operation Date (COD)", "Management", "Milestone", 0)
    for sb in steam_blows:
        L(sb, f"COM-{b}031")
    L(f"CON-{b}033", f"COM-{b}031"); L(f"CON-{b}034", f"COM-{b}031"); L("COM-0931", f"COM-{b}031")
    L(f"COM-{b}031", f"COM-{b}032"); L(f"COM-{b}032", f"COM-{b}033"); L(f"COM-{b}033", f"MS-{b}100")
    L(f"CON-{b}042", f"COM-{b}031")
    cod_ms.append(f"MS-{b}100")

A("MS-9999", "1.0 Milestones", "Project completion / plant COD", "Management", "Milestone", 0)
for m in cod_ms:
    L(m, "MS-9999")
L("CON-0951", "MS-9999"); L("COM-0951", "MS-9999")
L("CON-0002", "CON-0952", "FS", 120)

# --------------------------------------------------------------------------------------
# 2. CPM engine (FS / SS / FF with lags)
# --------------------------------------------------------------------------------------

def cpm(durations: dict[str, int], relations: pd.DataFrame,
        deadlines: dict[str, int] | None = None) -> pd.DataFrame:
    """Forward/backward pass. deadlines = finish-no-later-than constraints (can create negative float)."""
    deadlines = deadlines or {}
    succs, preds = defaultdict(list), defaultdict(list)
    indeg = {a: 0 for a in durations}
    for r in relations.itertuples():
        succs[r.predecessor].append(r)
        preds[r.successor].append(r)
        indeg[r.successor] += 1
    order, q = [], deque([a for a, d in indeg.items() if d == 0])
    while q:
        a = q.popleft(); order.append(a)
        for r in succs[a]:
            indeg[r.successor] -= 1
            if indeg[r.successor] == 0:
                q.append(r.successor)
    if len(order) != len(durations):
        raise ValueError("Logic loop detected")

    ES, EF = {}, {}
    for a in order:
        d = durations[a]
        es = 0
        for r in preds[a]:
            p = r.predecessor
            if r.rel_type == "FS": es = max(es, EF[p] + r.lag_days)
            elif r.rel_type == "SS": es = max(es, ES[p] + r.lag_days)
            elif r.rel_type == "FF": es = max(es, EF[p] + r.lag_days - d)
        ES[a], EF[a] = es, es + d

    finish = max(EF.values())
    LS, LF = {}, {}
    for a in reversed(order):
        d = durations[a]
        lf = finish
        for r in succs[a]:
            s = r.successor
            if r.rel_type == "FS": lf = min(lf, LS[s] - r.lag_days)
            elif r.rel_type == "SS": lf = min(lf, LS[s] - r.lag_days + d)
            elif r.rel_type == "FF": lf = min(lf, LF[s] - r.lag_days)
        if a in deadlines:
            lf = min(lf, deadlines[a])
        LF[a], LS[a] = lf, lf - d

    for a in HAMMOCKS:  # level-of-effort spans NTP to project completion
        ES[a], EF[a], LS[a], LF[a] = 0, finish, 0, finish
    return pd.DataFrame({
        "activity_id": order,
        "early_start": [ES[a] for a in order], "early_finish": [EF[a] for a in order],
        "late_start": [LS[a] for a in order], "late_finish": [LF[a] for a in order],
    }).assign(total_float=lambda d: d.late_start - d.early_start)


def pct_complete(start, finish, date):
    if finish <= start:
        return 1.0 if date >= finish else 0.0
    return min(1.0, max(0.0, (date - start) / (finish - start)))


# --------------------------------------------------------------------------------------
# 3. Build outputs
# --------------------------------------------------------------------------------------

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    act = pd.DataFrame(acts)
    rel = pd.DataFrame(rels)
    act["budget_pct_of_bac"] = (act.cost_weight / act.cost_weight.sum() * 100).round(4)
    # absorb rounding so the column sums to exactly 100
    act.loc[act.budget_pct_of_bac.idxmax(), "budget_pct_of_bac"] += round(100 - act.budget_pct_of_bac.sum(), 4)

    durations = dict(zip(act.activity_id, act.duration_days))
    first = cpm(durations, rel).set_index("activity_id")
    deadlines = {m: int(first.loc[m, "early_finish"]) for m in CONTRACT_MILESTONES}
    base = cpm(durations, rel, deadlines)
    base["critical"] = (base.total_float <= 0) & ~base.activity_id.isin(HAMMOCKS)
    base["near_critical"] = (base.total_float > 0) & (base.total_float <= NEAR_CRITICAL_FLOAT)
    base.insert(6, "duration_days", base.early_finish - base.early_start)
    base = act[["activity_id", "wbs", "activity_name", "discipline", "phase", "activity_type",
                "budget_pct_of_bac"]].merge(base, on="activity_id")

    # ---- Forecast / "actual" scenario at the data date --------------------------------
    # Documented, deterministic slippages so the dataset tells a clear story:
    slip = {
        "ENG-0003": 45,   # permits approved 45 days late
        "PRC-2111": 75,   # GT21 manufacturing delay at vendor - large, but mostly absorbed by float
        "PRC-2221": 35,   # HRSG22 pressure-parts delay - on the critical path, drives Block 2 COD
        "PRC-0902": 30,   # 400 kV GIS manufacturing slip
    }
    civil_productivity = 1.20   # civil works taking 20% longer than planned
    cost_factor = {"Civil": 1.12, "Mechanical": 1.04, "Electrical": 1.03,
                   "I&C": 1.02, "Process": 1.00, "Management": 1.06, "Commissioning": 1.00}

    fdur = {}
    for r in act.itertuples():
        d = r.duration_days + slip.get(r.activity_id, 0)
        if r.discipline == "Civil" and r.phase == "Construction":
            d = math.ceil(d * civil_productivity)
        fdur[r.activity_id] = d
    fcast_full = cpm(fdur, rel, deadlines)
    fc = fcast_full.rename(columns={"early_start": "forecast_start",
                                        "early_finish": "forecast_finish"})[
        ["activity_id", "forecast_start", "forecast_finish"]]

    prog = base.merge(fc, on="activity_id")
    prog["planned_pct_complete"] = [round(pct_complete(s, f, DATA_DATE) * 100, 1)
                                    for s, f in zip(prog.early_start, prog.early_finish)]
    prog["actual_pct_complete"] = [round(pct_complete(s, f, DATA_DATE) * 100, 1)
                                   for s, f in zip(prog.forecast_start, prog.forecast_finish)]
    prog["pv_pct_of_bac"] = (prog.budget_pct_of_bac * prog.planned_pct_complete / 100).round(4)
    prog["ev_pct_of_bac"] = (prog.budget_pct_of_bac * prog.actual_pct_complete / 100).round(4)
    prog["ac_pct_of_bac"] = (prog.ev_pct_of_bac * prog.discipline.map(cost_factor)).round(4)
    prog["finish_variance_days"] = prog.forecast_finish - prog.early_finish
    prog = prog.merge(fcast_full[["activity_id", "total_float"]].rename(
        columns={"total_float": "forecast_total_float"}), on="activity_id")
    prog.insert(0, "data_date_day", DATA_DATE)

    # ---- Monthly S-curve ---------------------------------------------------------------
    def cum_curve(df, s_col, f_col, day):
        return sum(bp * pct_complete(s, f, day)
                   for bp, s, f in zip(df.budget_pct_of_bac, df[s_col], df[f_col]))

    months = math.ceil(max(prog.forecast_finish.max(), prog.early_finish.max()) / 30)
    cpi_by_disc = prog.discipline.map(cost_factor)
    rows = []
    for m in range(0, months + 1):
        day = m * 30
        pv = cum_curve(prog, "early_start", "early_finish", day)
        fcst = cum_curve(prog, "forecast_start", "forecast_finish", day)
        ev = fcst if day <= DATA_DATE else None
        ac = (sum(bp * pct_complete(s, f, day) * k for bp, s, f, k in
                  zip(prog.budget_pct_of_bac, prog.forecast_start, prog.forecast_finish, cpi_by_disc))
              if day <= DATA_DATE else None)
        rows.append(dict(month=m, day=day, pv_cum_pct=round(pv, 2),
                         ev_cum_pct=None if ev is None else round(ev, 2),
                         ac_cum_pct=None if ac is None else round(ac, 2),
                         forecast_cum_pct=round(fcst, 2)))
    scurve = pd.DataFrame(rows)

    # ---- Write -------------------------------------------------------------------------
    act.drop(columns="cost_weight").to_csv(OUT / "activities.csv", index=False)
    rel.to_csv(OUT / "relationships.csv", index=False)
    base.to_csv(OUT / "baseline_cpm.csv", index=False)
    prog.to_csv(OUT / "progress_update.csv", index=False)
    scurve.to_csv(OUT / "monthly_s_curve.csv", index=False)

    # ---- Console summary ---------------------------------------------------------------
    pv, ev, ac = prog.pv_pct_of_bac.sum(), prog.ev_pct_of_bac.sum(), prog.ac_pct_of_bac.sum()
    print(f"Activities: {len(act)} | Relationships: {len(rel)}")
    print(f"Baseline finish: day {base.early_finish.max()} | Forecast finish: day {prog.forecast_finish.max()}")
    print(f"Critical: {base.critical.sum()} | Near-critical (<= {NEAR_CRITICAL_FLOAT}d): {base.near_critical.sum()}")
    for m in CONTRACT_MILESTONES:
        r = prog.set_index("activity_id").loc[m]
        print(f"{m}: baseline day {r.early_finish} -> forecast day {r.forecast_finish} ({r.finish_variance_days:+d} d)")
    print(f"At data date day {DATA_DATE}: PV {pv:.2f}% | EV {ev:.2f}% | AC {ac:.2f}% "
          f"| SPI {ev/pv:.2f} | CPI {ev/ac:.2f}")


if __name__ == "__main__":
    main()
