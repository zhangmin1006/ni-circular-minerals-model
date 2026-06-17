"""
Material Flow Account (MFA) for the NI Circular Minerals MVM.

Physical backbone of the ABM. For each mineral it tracks, per year:

  primary extraction + imports + recycled  ->  demand (use)
  end-of-life arisings -> collection -> recovery -> secondary material

and an in-use stock that accumulates and later returns as end-of-life arisings
after a product lifetime delay. Mass balance is checked every year.

Supply-share indicators (domestic / recycled / single-country import) feed the
Vision 2035 target comparison for question 2.4.

All stock/flow seed values are PROXY (UK data scaled to NI). STATUS in register.
"""

import numpy as np
import seed_parameters as P

# Minerals whose end-of-life collection is dominated by WEEE/battery/ELV streams,
# so their collection rate is capped at the real WEEE collection rate
# (seed_parameters.COLLECTION_RATE_WEEE). Copper/aluminium/nickel have large
# non-WEEE scrap streams and are not capped here.
WEEE_STREAM_MINERALS = {"REE_magnet", "Lithium", "Cobalt"}


# Per-mineral seed parameters (PROXY). tonnes/yr unless noted.
# demand0: NI annual demand baseline; lifetime: yrs to end-of-life;
# coll: collection rate; rec: recovery yield; dom0: domestic primary share;
# imp_conc: max single-country import concentration (HHI proxy, 0-1).
# imp_conc for REE/Li/Co anchored to 2023 global mine-supply concentration
# (China 74% REE, Australia 44% Li, DRC 70% Co; BGS/Idoine et al. 2025, via the
# GSNI "Critical Minerals & the Circular Economy in NI" briefing 2025).
MINERAL_PARAMS = {
    #              demand0 lifetime coll  rec   dom0  imp_conc
    "REE_magnet": ( 120.0,   10,   0.05, 0.85, 0.00, 0.74),
    "Lithium":    ( 300.0,    8,   0.08, 0.50, 0.00, 0.44),
    "Cobalt":     (  90.0,    8,   0.10, 0.55, 0.00, 0.70),
    "Nickel":     ( 800.0,   12,   0.30, 0.60, 0.05, 0.40),
    "Copper":     (9000.0,   25,   0.45, 0.90, 0.02, 0.30),
    "Aluminium":  (12000.0,  20,   0.42, 0.75, 0.00, 0.35),
    "Antimony":   (  40.0,    7,   0.02, 0.40, 0.00, 0.70),
    "Baryte":     (5000.0,    5,   0.00, 0.10, 0.30, 0.45),
    "Salt":       (200000.0,  1,   0.00, 0.00, 0.95, 0.20),
    "Zinc":       (3000.0,   20,   0.35, 0.70, 0.02, 0.40),
}


# Proxy commodity prices (GBP per tonne) to convert physical flows -> economic
# value for the I-O demand vector. STATUS: PROXY (replace with LME/USGS/trade).
MINERAL_PRICE_GBP_PER_T = {
    "REE_magnet": 90000.0, "Lithium": 18000.0, "Cobalt": 28000.0,
    "Nickel": 16000.0, "Copper": 8000.0, "Aluminium": 2200.0,
    "Antimony": 11000.0, "Baryte": 250.0, "Salt": 60.0, "Zinc": 2500.0,
}


class MFA:
    def __init__(self, use_ree_pilot=False):
        params = {k: v for k, v in MINERAL_PARAMS.items()}
        # Recovery yields are now read from data_register.csv (single source of
        # truth) rather than the literals above, for the minerals the register
        # tracks (REE_magnet, Lithium, Copper).
        for mineral, yield_ in P.RECOVERY_YIELDS.items():
            if mineral in params and yield_ is not None:
                d0, life, coll, _rec, dom0, imp = params[mineral]
                params[mineral] = (d0, life, coll, yield_, dom0, imp)
        prices = dict(MINERAL_PRICE_GBP_PER_T)
        if use_ree_pilot:
            # ground the REE_magnet thread in the pilot dataset
            import os, sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
            import ree_pilot
            ree_pilot.apply_to_mineral_params(params)
            ree_pilot.apply_price(prices)
        self.minerals = list(params.keys())
        self.p = params
        self.prices = prices
        # in-use stock seeded as lifetime x demand (steady-state approximation)
        self.stock = {m: self.p[m][0] * self.p[m][1] for m in self.minerals}
        # ring buffer of past inflows to age into end-of-life arisings
        self._inflow_hist = {m: [self.p[m][0]] * self.p[m][1] for m in self.minerals}
        self.history = []

    def step(self, year, demand_multiplier=None,
             collection_boost=None, recovery_boost=None, new_domestic=None,
             import_constraint=None, diversification=0.0):
        """Advance one year. Optional dicts override per-mineral behaviour
        (these are the levers the ABM/policy layer pushes).

        `import_constraint` models an UPSTREAM SUPPLY SHOCK: {mineral: max import
        as a fraction of demand}. If domestic + recycled + (capped) imports cannot
        meet demand, the shortfall is recorded as `unmet_demand_t` (the supply gap
        that hits downstream firms) rather than being silently imported."""
        demand_multiplier = demand_multiplier or {}
        collection_boost = collection_boost or {}
        recovery_boost = recovery_boost or {}
        new_domestic = new_domestic or {}
        import_constraint = import_constraint or {}

        rows = []
        for m in self.minerals:
            demand0, lifetime, coll, rec, dom0, imp_conc = self.p[m]
            demand = demand0 * demand_multiplier.get(m, 1.0)

            # end-of-life arisings: product placed on market 'lifetime' yrs ago
            eol = self._inflow_hist[m][0] if self._inflow_hist[m] else 0.0

            coll_rate = min(0.95, coll + collection_boost.get(m, 0.0))
            # minerals recovered mainly from WEEE/battery/ELV streams cannot be
            # collected beyond the real WEEE collection rate (UK ~25%, register).
            if m in WEEE_STREAM_MINERALS:
                coll_rate = min(coll_rate, P.COLLECTION_RATE_WEEE)
            rec_rate = min(0.98, rec + recovery_boost.get(m, 0.0))
            collected = eol * coll_rate
            recycled = collected * rec_rate

            # domestic primary (can be raised by ABM opening a mine)
            dom_share = min(1.0, dom0 + new_domestic.get(m, 0.0))
            domestic_primary = demand * dom_share

            # Domestic primary is allocated first; recycled material can only
            # satisfy remaining demand. This prevents high-domestic/high-recovery
            # cases from over-supplying and breaking the mass-balance identity.
            demand_after_domestic = max(0.0, demand - domestic_primary)
            supplied_secondary = min(recycled, demand_after_domestic)
            remaining = max(0.0, demand - supplied_secondary - domestic_primary)
            # upstream supply shock: cap available imports -> any shortfall is unmet
            cap = import_constraint.get(m)
            if cap is not None:
                imports = min(remaining, max(0.0, cap) * demand)
            else:
                imports = remaining
            unmet = remaining - imports                  # supply gap (downstream hit)

            # supply shares (for Vision 2035 indicators / Q2.4)
            recycled_share = supplied_secondary / demand if demand else 0.0
            domestic_share = domestic_primary / demand if demand else 0.0
            import_share = imports / demand if demand else 0.0
            supply_gap_share = unmet / demand if demand else 0.0
            # international diversification (partnerships) lowers the share of
            # imports from the single dominant country. Max cut 0.45 at full lever,
            # calibrated to Japan's coordinated post-2010 effort: China REE
            # dependence fell from ~90% to ~58% (~36%) and is now targeted below
            # 50% (~44%) via overseas equity/offtake + recycling + substitution.
            eff_imp_conc = imp_conc * (1.0 - 0.45 * max(0.0, min(1.0, diversification)))
            single_country_exposure = import_share * eff_imp_conc

            # update in-use stock and age the inflow history (only supplied material
            # enters use; unmet demand does not)
            inflow = demand - unmet
            self.stock[m] += inflow - eol
            self._inflow_hist[m].append(inflow)
            self._inflow_hist[m].pop(0)

            rows.append({
                "year": year, "mineral": m,
                "demand_t": demand,
                "domestic_primary_t": domestic_primary,
                "imports_t": imports,
                "recycled_t": supplied_secondary,
                "eol_arisings_t": eol,
                "collected_t": collected,
                "in_use_stock_t": self.stock[m],
                "unmet_demand_t": unmet,
                "domestic_share": domestic_share,
                "recycled_share": recycled_share,
                "import_share": import_share,
                "supply_gap_share": supply_gap_share,
                "single_country_exposure": single_country_exposure,
                "mass_balance_ok": abs((domestic_primary + imports + supplied_secondary
                                        + unmet) - demand) < 1e-6,
            })
        self.history.extend(rows)
        return rows

    def supply_security_summary(self, rows):
        """Aggregate weighted shares for the Vision 2035 dashboard (Q2.4)."""
        tot = sum(r["demand_t"] for r in rows) or 1.0
        return {
            "recycled_share": sum(r["recycled_t"] for r in rows) / tot,
            "domestic_share": sum(r["domestic_primary_t"] for r in rows) / tot,
            "import_share": sum(r["imports_t"] for r in rows) / tot,
            "supply_gap_share": sum(r.get("unmet_demand_t", 0.0) for r in rows) / tot,
            "max_single_country_exposure": max(r["single_country_exposure"] for r in rows),
        }


if __name__ == "__main__":
    mfa = MFA()
    rows = mfa.step(2026)
    s = mfa.supply_security_summary(rows)
    print("Year 2026 supply shares (demand-weighted):")
    for k, v in s.items():
        print(f"  {k:28s} {v:6.3f}")
    print("All mass balances OK:", all(r["mass_balance_ok"] for r in rows))
