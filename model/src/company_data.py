"""
Company evidence layer for the NI circular minerals model.

The register is a desk-researched, web-verified starting point. Numeric fields
are bounded calibration hints unless an official audited value is available.
They make the ABM less anonymous while keeping the uncertainty visible.
"""

import csv
import math
import os
from collections import Counter, defaultdict

import seed_parameters as P


REGISTER_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "company_register.csv")
CONFIDENCE = {"web_verified": 1.0, "desk_verified": 0.75, "proxy": 0.5}
MINING_ROLES = {
    "mining_exploration", "mining_operator", "quarry_mineral_processor",
    "quarry_materials",
}
RECYCLING_ROLES = {"critical_mineral_recycler", "waste_recycler"}
DOWNSTREAM_ROLES = {"downstream_manufacturer", "supply_chain_manufacturer"}


def load_company_register(path=REGISTER_PATH):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, skipinitialspace=True))


# Map the register's mineral/product tags to a model sector, so firm headcounts
# can be folded into the spatial employment layer.
ROLE_SECTOR = {
    "critical_mineral_recycler": "Recycling_Secondary",
    "waste_recycler": "Recycling_Secondary",
    "mining_exploration": "Mining_Quarrying",
    "mining_operator": "Mining_Quarrying",
    "quarry_mineral_processor": "Mining_Quarrying",
    "quarry_materials": "Mining_Quarrying",
    "downstream_manufacturer": "Manufacturing",
    "supply_chain_manufacturer": "Manufacturing",
}
# Lifecycle stages that are not yet producing get down-weighted when used as
# real evidence (e.g. Dalradian's proposed mine).
LIFECYCLE_WEIGHT = {
    "operating": 1.0, "scale_up": 0.9, "transition": 0.8, "care_and_maintenance": 0.5,
    "exploration": 0.4, "proposed": 0.5,
}


def company_context(rows=None):
    rows = rows or load_company_register()
    counts = companies_by_role(rows)
    capex = firm_capital_pipeline(rows)
    return {
        "company_count": len(rows),
        "company_mining_count": sum(counts[r] for r in MINING_ROLES),
        "company_recycler_count": sum(counts[r] for r in RECYCLING_ROLES),
        "company_downstream_count": sum(counts[r] for r in DOWNSTREAM_ROLES),
        "company_employee_estimate": round(sum(_number(r, "employee_estimate") for r in rows), 0),
        "company_proposed_mining_jobs": round(sum(
            _number(r, "employee_estimate") for r in rows
            if r["role"] in MINING_ROLES and r.get("lifecycle_stage") == "proposed"), 0),
        "company_capex_pipeline_gbp_m": capex["total_gbp_m"],
        "company_capex_operating_gbp_m": capex["operating_gbp_m"],
        "company_capex_proposed_gbp_m": capex["proposed_gbp_m"],
        "company_recycler_capacity_tpa": round(
            sum(recycler_installed_capacity_t(rows).values()), 0),
        "avg_recycler_capacity_score": _weighted_score(
            rows, "capacity_score", RECYCLING_ROLES),
        "avg_feedstock_score": _weighted_score(rows, "feedstock_score", RECYCLING_ROLES),
        "avg_downstream_demand_score": _weighted_score(
            rows, "demand_score", DOWNSTREAM_ROLES),
        "avg_local_procurement_score": _weighted_score(
            rows, "local_procurement_score", None),
        "avg_planning_risk_score": _weighted_score(
            rows, "planning_risk_score", MINING_ROLES),
    }


def firm_capital_pipeline(rows=None):
    """Investment (£m) named in the register, split by lifecycle, so Q2.6 can
    report a firm-grounded capital pipeline (Dalradian £250m, Mannok £330m,
    Seagate £115m, Wrightbus £25m, Spirit £439m...)."""
    rows = rows or load_company_register()
    total = operating = proposed = 0.0
    for r in rows:
        inv = _number(r, "investment_gbp_m")
        if inv <= 0:
            continue
        total += inv
        if r.get("lifecycle_stage") in ("proposed", "exploration"):
            proposed += inv
        else:
            operating += inv
    return {
        "total_gbp_m": round(total, 1),
        "operating_gbp_m": round(operating, 1),
        "proposed_gbp_m": round(proposed, 1),
    }


def recycler_installed_capacity_t(rows=None):
    """Installed secondary-processing capacity (tonnes/yr) by tracked mineral,
    from named recyclers' reported plant capacity (currently Ionic's 400 tpa
    separated rare-earth oxide plant in Belfast)."""
    rows = rows or load_company_register()
    cap = defaultdict(float)
    for r in rows:
        if r["role"] not in RECYCLING_ROLES:
            continue
        tpa = _number(r, "annual_capacity_tonnes")
        if tpa <= 0:
            continue
        minerals = _minerals(r)
        if "REE_magnet" in minerals:
            cap["REE_magnet"] += tpa
    return {m: v for m, v in cap.items() if m in P.MINERALS}


def firm_recycling_output_floor_gbp_m(prices, rows=None):
    """A firm-grounded floor (£m/yr) on recycling-sector output, from installed
    plant capacity x commodity price x a capacity-score utilisation factor.
    Used so the recycling sector's economic activity is never below what named
    NI plants already represent, regardless of modelled domestic end-of-life."""
    rows = rows or load_company_register()
    floor = 0.0
    util = _weighted_score(rows, "capacity_score", RECYCLING_ROLES) or 0.5
    for mineral, tpa in recycler_installed_capacity_t(rows).items():
        price_m = prices.get(mineral, 0.0) / 1e6      # £m per tonne
        floor += tpa * price_m * util
    return round(floor, 3)


def firm_district_employment(rows=None):
    """Confidence- and lifecycle-weighted firm headcount by (sector, district),
    for grounding the spatial employment allocation in real firm locations."""
    rows = rows or load_company_register()
    out = defaultdict(lambda: defaultdict(float))
    for r in rows:
        sector = ROLE_SECTOR.get(r["role"])
        district = (r.get("district") or "").strip()
        if not sector or not district or district == "Multiple":
            continue
        emp = _number(r, "employee_estimate")
        if emp <= 0:
            continue
        weight = (CONFIDENCE.get(r.get("evidence_status"), 0.75)
                  * LIFECYCLE_WEIGHT.get(r.get("lifecycle_stage"), 1.0))
        out[sector][district] += emp * weight
    return {sector: dict(d) for sector, d in out.items()}


def companies_by_role(rows=None):
    rows = rows or load_company_register()
    return Counter(r["role"] for r in rows)


def mineral_project_properties(rows=None):
    rows = rows or load_company_register()
    props = defaultdict(lambda: {"resource": [], "capacity": [], "risk": [], "local": []})
    for row in rows:
        if row["role"] not in MINING_ROLES:
            continue
        confidence = CONFIDENCE.get(row.get("evidence_status"), 0.75)
        for mineral in _minerals(row):
            if mineral not in P.MINERALS:
                continue
            props[mineral]["resource"].append(_score(row, "resource_score") * confidence)
            props[mineral]["capacity"].append(_score(row, "capacity_score") * confidence)
            props[mineral]["risk"].append(_score(row, "planning_risk_score"))
            props[mineral]["local"].append(_score(row, "local_procurement_score"))

    out = {}
    for mineral, vals in props.items():
        resource = _mean(vals["resource"])
        capacity = _mean(vals["capacity"])
        risk = _mean(vals["risk"])
        local = _mean(vals["local"])
        out[mineral] = {
            "deposit_quality": round(0.65 * resource + 0.35 * capacity, 3),
            "project_risk": round(risk, 3),
            "local_procurement": round(local, 3),
            "output_share": round(max(0.03, min(0.18, 0.05 + 0.13 * capacity)), 3),
        }
    return out


def deposit_quality_by_mineral(rows=None):
    return {
        mineral: props["deposit_quality"]
        for mineral, props in mineral_project_properties(rows).items()
    }


# Which tracked minerals a recycler addresses, inferred from its feedstock tags.
FEEDSTOCK_MINERALS = {
    "REE_magnet": {"REE_magnet"},
    "WEEE_batteries_ELV_feedstock": {"Lithium", "Cobalt", "Nickel", "Copper", "Aluminium"},
    "commercial_recyclables": {"Copper", "Aluminium"},
    "Glass_cullet": set(),   # bulk circularity, no tracked critical mineral
}


def recycler_targets(products, universe=None):
    """Tracked minerals a recycler with these feedstock tags can address."""
    universe = universe or P.MINERALS
    targets = set()
    for tag in products:
        targets |= FEEDSTOCK_MINERALS.get(tag, set())
    return {m for m in targets if m in universe}


SCORE_COLUMNS = (
    "resource_score", "capacity_score", "feedstock_score", "demand_score",
    "local_procurement_score", "planning_risk_score", "skills_intensity_score",
    "circularity_score",
)


def parse_firm(row):
    """Normalise one register row into a typed firm record for the ABM agents."""
    products = _minerals(row)
    return {
        "name": (row.get("company") or "").strip(),
        "role": (row.get("role") or "").strip(),
        "sector": (row.get("sector") or "").strip(),
        "district": (row.get("district") or "").strip(),
        "lifecycle": (row.get("lifecycle_stage") or "").strip(),
        "products": products,
        "minerals": {m for m in products if m in P.MINERALS},
        "recycler_targets": recycler_targets(products),
        "employees": _number(row, "employee_estimate"),
        "investment_gbp_m": _number(row, "investment_gbp_m"),
        "capacity_tonnes": _number(row, "annual_capacity_tonnes"),
        "confidence": CONFIDENCE.get(row.get("evidence_status"), 0.75),
        "scores": {c[:-6]: _score(row, c) for c in SCORE_COLUMNS},  # drop "_score"
    }


def parse_firms(rows=None):
    return [parse_firm(r) for r in (rows or load_company_register())]


def recycler_focus_minerals(rows=None):
    rows = rows or load_company_register()
    focus = set()
    for row in rows:
        if row["role"] not in RECYCLING_ROLES:
            continue
        focus |= recycler_targets(_minerals(row))
    return sorted(focus.intersection(P.CRITICAL_MINERALS), key=P.CRITICAL_MINERALS.index)


def recycler_capacity_by_mineral(rows=None):
    rows = rows or load_company_register()
    mineral_scores = defaultdict(list)
    for row in rows:
        if row["role"] not in RECYCLING_ROLES:
            continue
        score = 0.55 * _score(row, "capacity_score") + 0.45 * _score(row, "feedstock_score")
        for mineral in recycler_targets(_minerals(row)):
            if mineral in P.CRITICAL_MINERALS:
                mineral_scores[mineral].append(score)
    return {m: round(_mean(v), 3) for m, v in mineral_scores.items()}


def local_procurement_baseline(rows=None):
    rows = rows or load_company_register()
    score = _weighted_score(rows, "local_procurement_score", None)
    return round(max(0.0, min(0.08, 0.015 + 0.06 * score)), 4)


def downstream_demand_signal(rows=None):
    rows = rows or load_company_register()
    selected = [r for r in rows if r["role"] in DOWNSTREAM_ROLES]
    if not selected:
        return 1.0
    weighted = sum(
        _score(r, "demand_score") * math.log1p(max(0.0, _number(r, "employee_estimate")))
        for r in selected
    )
    normaliser = sum(math.log1p(max(0.0, _number(r, "employee_estimate"))) for r in selected) or 1.0
    return round(1.0 + 0.08 * weighted / normaliser, 4)


def _weighted_score(rows, column, roles):
    selected = [r for r in rows if roles is None or r["role"] in roles]
    if not selected:
        return 0.0
    weights = [math.log1p(max(0.0, _number(r, "employee_estimate"))) or 1.0 for r in selected]
    values = [_score(r, column) * CONFIDENCE.get(r.get("evidence_status"), 0.75) for r in selected]
    return sum(v * w for v, w in zip(values, weights)) / sum(weights)


def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _score(row, column, default=0.5):
    return max(0.0, min(1.0, _number(row, column, default)))


def _number(row, column, default=0.0):
    value = row.get(column, "")
    if value in ("", None):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _minerals(row):
    return {
        item.strip()
        for item in row.get("minerals_or_products", "").split(";")
        if item.strip()
    }
