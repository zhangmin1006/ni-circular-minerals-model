"""
Economic-negative-impact layer for consultation question 2.7:
"What are the potential ECONOMIC negative impacts of mineral development?"

This module focuses ONLY on the *economic* downsides of (primarily) primary
mineral extraction — not the environmental pressures (those are tracked by the
I-O CO2/PM satellites and are out of scope here). Each impact is grounded in the
Minviro Final Report / Appendix A:

  1. Benefit leakage (enclave economy)  -- Minviro sec 2.2.5 "Retained employment"
     + the Galmoy/Lisheen comparison: GVA/jobs leak out of NI when specialist
     labour and equipment are imported.  leak = (1 - retention) x minerals GVA.
  2. Closure cliff + remediation liability -- Minviro sec 1.4.6.8 "Mine Closure"
     (Fig 1.33 closure-cost estimates): a mine's direct GVA/jobs END at closure
     (a local boom-bust cliff within the 30-yr horizon), and remediation is a
     public liability if not bonded.
  3. Agriculture & tourism displacement -- Minviro sec 3.4.2.4 / 3.4.2.5: a mine's
     land take and amenity loss displace host-area farming and tourism output.
  4. Boom-bust / price-volatility exposure -- Minviro/Appendix A "price volatility",
     "volatile inflows": commodity-price swings put mining revenue/GVA at risk.
  5. Stranded / sunk capital on contested long-lead projects -- e.g. Dalradian's
     Curraghinalt (~GBP250m proposed, ~21-yr planning inquiry): capital exposed to
     never operating, or to being stranded mid-life by recycling/substitution or a
     price collapse. A circular (recovery-capacity) hedge lowers this exposure.

All magnitudes are PROXY/desk values (data_register), so the credible content is
the RELATIVE contrast — primary extraction carries high economic-negative risk;
recycling/circular activity carries little; and responsible, *managed* development
(bonded closure, progressive rehabilitation, local content + skills) mitigates it.
"""

import data_register as DR

# --- parameters (PROXY/desk, Minviro-grounded; see data_register.csv) ----------
MINE_OPERATING_LIFE_YEARS = DR.value("mine_operating_life_years", 18.0)
CLOSURE_REMEDIATION_GBP_PER_MINE = DR.value("closure_remediation_gbp_per_mine", 35.0)
AGRI_TOURISM_DISPLACEMENT_GBP_PER_MINE_PA = DR.value(
    "agri_tourism_displacement_gbp_per_mine_pa", 3.0)
COMMODITY_PRICE_VOLATILITY = DR.value("commodity_price_volatility", 0.30)
MINING_WAGE_PREMIUM = DR.value("mining_wage_premium", 0.35)
CONTESTED_PROJECT_CAPITAL_GBP_M = DR.value("contested_project_capital_gbp_m", 250.0)
BASE_LOCAL_RETENTION = DR.value("mining_benefit_retention_base", 0.70)

# components reported (for the dashboard / memo ordering)
COMPONENTS = ("benefit_leakage", "closure_liability", "agri_tourism_displacement")
RISK_EXPOSURES = ("boom_bust_var", "stranded_capital_at_risk")


def management_intensity(policy):
    """0-1 'responsible-management' intensity from the community-benefit and ESG
    levers — drives bonded closure and progressive rehabilitation (which cut the
    closure liability and shorten displacement)."""
    cb = policy.get("community_benefit", 0.0)
    esg = min(1.0, policy.get("esg_cost", 0.0) / 0.18)   # 0.18 ~ high-ESG stance
    return max(0.0, min(1.0, 0.5 * cb + 0.5 * esg))


def local_retention(policy):
    """Share of minerals GVA/jobs retained in NI (mirrors employment_module):
    rises with local-supplier development and a local skills pipeline."""
    return min(0.98, BASE_LOCAL_RETENTION
               + 0.20 * policy.get("local_supplier_support", 0.0)
               + 0.10 * policy.get("skills_support", 0.0))


def circular_hedge(policy):
    """0-1 proxy for recovery-capacity build-out that hedges reliance on a single
    contested mine (lowers stranded-capital exposure)."""
    return max(0.0, min(1.0,
               0.6 * policy.get("recycling_grant", 0.0)
               + 0.3 * policy.get("collection_infrastructure", 0.0)
               + 0.4 * policy.get("innovation_grant", 0.0)))


def benefit_leakage_gbp_m(minerals_gva, retention):
    """Discounted GVA that leaks out of NI (imported specialist labour/equipment)."""
    return max(0.0, (1.0 - retention) * minerals_gva)


def closure_liability_gbp_m(mines_opened, mgmt):
    """Remediation/closure cost falling on the public purse if not bonded; a
    responsible-management stance bonds it, cutting the public liability."""
    return max(0.0, mines_opened) * CLOSURE_REMEDIATION_GBP_PER_MINE * (1.0 - mgmt)


def displacement_gbp_m(disc_active_mine_years, mgmt):
    """Host-area agriculture + tourism GVA displaced (discounted active-mine-years
    x per-mine-year displacement). Progressive rehabilitation (management) shortens
    the displaced period, cutting it by up to half."""
    return max(0.0, disc_active_mine_years) * AGRI_TOURISM_DISPLACEMENT_GBP_PER_MINE_PA * (1.0 - 0.5 * mgmt)


def boom_bust_var_gbp_m(end_mining_gva):
    """Annual mining GVA exposed to commodity-price volatility (revenue-at-risk)."""
    return COMMODITY_PRICE_VOLATILITY * max(0.0, end_mining_gva)


def stranded_capital_gbp_m(mines_opened, hedge):
    """Contested-project capital at risk of being sunk-without-operating or
    stranded mid-life; only material when a contested mine is actually developed,
    and reduced by a circular (recovery-capacity) hedge."""
    if mines_opened < 1:
        return 0.0
    strand_prob = 0.5 * (1.0 - 0.6 * max(0.0, min(1.0, hedge)))
    return CONTESTED_PROJECT_CAPITAL_GBP_M * strand_prob
