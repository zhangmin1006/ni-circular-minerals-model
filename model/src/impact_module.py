"""
Negative-impact layer for consultation question 2.7.

The I-O already carries validated CO2 (ktCO2e) and PM (t) satellites. This module
adds the other Minviro Appendix A impact groups that the I-O has no physical
satellite for — water, land transformation, biodiversity pressure and mine
waste/tailings — as RELATIVE pressure indices, and an ESG-mitigation factor.

Per Minviro Appendix A: the ultimate receptors are people and biodiversity;
impacts are SITE-SPECIFIC (depend on receptors, design, operation and closure);
and primary mining is land/water/biodiversity/waste-intensive while recycling's
footprint is mainly energy/CO2 (~30% of the primary footprint). The indices are
dimensionless, mining-referenced PROXIES — the credible content is the relative
contrast (primary >> recycling) and the impact-per-£GVA eco-efficiency.
"""

# Relative environmental pressure per £m of (priced) domestic activity, by pathway.
PRESSURE = {
    "mining":        {"water": 6.0, "land": 10.0, "biodiversity": 8.0, "waste": 50.0},
    "recycling":     {"water": 1.2, "land": 0.6,  "biodiversity": 0.4, "waste": 2.0},
    "manufacturing": {"water": 1.5, "land": 0.6,  "biodiversity": 0.5, "waste": 1.5},
}
CATEGORIES = ("water", "land", "biodiversity", "waste")

# Magnet-to-magnet / secondary recycling LCA vs primary mine+refine (ree_pilot;
# Minviro CLCA template) — recycling ~30% of the primary carbon footprint.
RECYCLING_CO2_VS_PRIMARY = 0.30

# High-ESG / low-impact design (water recycling, progressive rehabilitation,
# biodiversity net gain, dust/noise controls, closure planning) can cut the
# local pressures of a given activity by up to this fraction. PROXY.
ESG_MAX_MITIGATION = 0.35
ESG_REF = 0.15            # esg_cost lever level at which mitigation is ~maxed


def esg_mitigation(esg_cost=0.0):
    """Multiplier (<=1) applied to primary-mining local pressures under a high-ESG
    stance. esg_cost 0 -> 1.0 (no mitigation); >=ESG_REF -> 1-ESG_MAX_MITIGATION."""
    return 1.0 - ESG_MAX_MITIGATION * min(1.0, max(0.0, esg_cost) / ESG_REF)


def annual_pressures(mining_fd, recycling_fd, manuf_fd=0.0, esg_cost=0.0):
    """Relative pressure indices for one year from priced domestic activity
    (£m): mining final demand, recycling final demand, manufacturing. High-ESG
    mitigation is applied to the mining (primary) component only."""
    mit = esg_mitigation(esg_cost)
    out = {}
    for cat in CATEGORIES:
        out[cat] = (mining_fd * PRESSURE["mining"][cat] * mit
                    + recycling_fd * PRESSURE["recycling"][cat]
                    + manuf_fd * PRESSURE["manufacturing"][cat])
    return out
