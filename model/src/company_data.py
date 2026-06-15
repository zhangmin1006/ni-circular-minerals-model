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


def company_context(rows=None):
    rows = rows or load_company_register()
    counts = companies_by_role(rows)
    return {
        "company_count": len(rows),
        "company_mining_count": sum(counts[r] for r in MINING_ROLES),
        "company_recycler_count": sum(counts[r] for r in RECYCLING_ROLES),
        "company_downstream_count": sum(counts[r] for r in DOWNSTREAM_ROLES),
        "company_employee_estimate": round(sum(_number(r, "employee_estimate") for r in rows), 0),
        "company_proposed_mining_jobs": round(sum(
            _number(r, "employee_estimate") for r in rows
            if r["role"] in MINING_ROLES and r.get("lifecycle_stage") == "proposed"), 0),
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


def recycler_focus_minerals(rows=None):
    rows = rows or load_company_register()
    focus = set()
    for row in rows:
        if row["role"] not in RECYCLING_ROLES:
            continue
        minerals = _minerals(row)
        if "REE_magnet" in minerals:
            focus.add("REE_magnet")
        if "WEEE_batteries_ELV_feedstock" in minerals:
            focus.update({"Lithium", "Cobalt", "Nickel", "Copper", "Aluminium"})
        if "commercial_recyclables" in minerals:
            focus.update({"Copper", "Aluminium"})
    return sorted(focus.intersection(P.CRITICAL_MINERALS), key=P.CRITICAL_MINERALS.index)


def recycler_capacity_by_mineral(rows=None):
    rows = rows or load_company_register()
    mineral_scores = defaultdict(list)
    for row in rows:
        if row["role"] not in RECYCLING_ROLES:
            continue
        score = 0.55 * _score(row, "capacity_score") + 0.45 * _score(row, "feedstock_score")
        minerals = _minerals(row)
        targets = set()
        if "REE_magnet" in minerals:
            targets.add("REE_magnet")
        if "WEEE_batteries_ELV_feedstock" in minerals:
            targets.update({"Lithium", "Cobalt", "Nickel", "Copper", "Aluminium"})
        if "commercial_recyclables" in minerals:
            targets.update({"Copper", "Aluminium"})
        for mineral in targets:
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
