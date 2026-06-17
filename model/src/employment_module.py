"""
Employment, skills & regional-growth layer for consultation question 2.5.

Turns the model's jobs-by-sector output into the Q2.5 indicators the proposal
asks for: jobs by skill level, wage bill and wage premium, retained local
employment (the Minviro leakage fix), and a training/apprenticeship need.

All splits are PROXY (ONS SOC / ASHE-by-industry structure), flagged in
data_register.csv; the wage anchor is the real NISRA ASHE NI median.
"""

# Real wage anchor: NISRA ASHE 2024 median FT gross weekly £666 -> annual.
NI_MEDIAN_ANNUAL_WAGE = 34632.0          # £ (NISRA ASHE Apr 2024; UK was £37,430)

# Sector wage index relative to the NI median FT wage. PROXY, ordered by the
# well-established ONS ASHE-by-industry ranking: mining & quarrying is among the
# highest-paid industries; manufacturing pays a modest premium; recycling/waste
# sits around the median.
SECTOR_WAGE_INDEX = {
    "Mining_Quarrying": 1.35,
    "Recycling_Secondary": 1.00,
    "Manufacturing": 1.10,
}

# Skill-level composition (high / mid / entry) per sector. PROXY (ONS SOC for
# SIC B / C / E). Mining & advanced manufacturing are skill-intensive
# (engineers, geoscientists, process technicians); recycling is more mixed.
SKILL_SPLIT = {
    "Mining_Quarrying": (0.30, 0.45, 0.25),
    "Recycling_Secondary": (0.20, 0.45, 0.35),
    "Manufacturing": (0.35, 0.45, 0.20),
}
_DEFAULT_SPLIT = (0.25, 0.50, 0.25)


def skill_breakdown(jobs_by_sector):
    """jobs_by_sector: {sector: n}. -> {'high','mid','entry'} job counts."""
    out = {"high": 0.0, "mid": 0.0, "entry": 0.0}
    for sector, n in jobs_by_sector.items():
        hi, mid, en = SKILL_SPLIT.get(sector, _DEFAULT_SPLIT)
        out["high"] += n * hi
        out["mid"] += n * mid
        out["entry"] += n * en
    return out


def wage_metrics(jobs_by_sector):
    """-> dict: total annual wage bill (£m), average wage (£), premium vs NI median."""
    bill = 0.0
    total = 0.0
    for sector, n in jobs_by_sector.items():
        wage = NI_MEDIAN_ANNUAL_WAGE * SECTOR_WAGE_INDEX.get(sector, 1.0)
        bill += n * wage
        total += n
    avg = bill / total if total else 0.0
    return {
        "wage_bill_gbp_m": round(bill / 1e6, 2),
        "avg_wage_gbp": round(avg, 0),
        "wage_premium_vs_ni": round(avg / NI_MEDIAN_ANNUAL_WAGE, 3) if total else 0.0,
    }


def retained_local(total_jobs, local_supplier_support=0.0, skills_support=0.0):
    """Share of jobs filled by NI residents (vs imported/commuting specialist
    labour — Minviro's leakage point). Local supplier development and a local
    skills pipeline raise retention. PROXY: 0.70 base -> up to 0.98."""
    retention = min(0.98, 0.70 + 0.20 * local_supplier_support
                    + 0.10 * skills_support)
    return round(total_jobs * retention, 1), round(retention, 3)


def training_need(delta_jobs, jobs_by_sector):
    """Annual skilled-role training/apprenticeship need = job growth × the
    skilled (high+mid) share of the sector mix."""
    sk = skill_breakdown(jobs_by_sector)
    tot = sum(sk.values()) or 1.0
    skilled_share = (sk["high"] + sk["mid"]) / tot
    return round(max(0.0, delta_jobs) * skilled_share, 1)
