"""
Coupling + indicator layer for the NI Circular Minerals MVM (Tier 1).

Runs the annual soft-link loop:
    ABM (decisions) -> MFA (physical flows) -> dynamic I-O (economic/enviro impact)
and assembles indicators mapped to consultation questions 2.1-2.7.

CGE feedback (prices, wages) is a Tier-2/3 addition; here the price_index is an
exogenous scenario path. Discounting uses the STPR (3.5%).
"""

import numpy as np
import pandas as pd
import seed_parameters as P
from io_module import DynamicIO
from mfa_module import MFA, MINERAL_PRICE_GBP_PER_T
from abm_module import MineralsABM
from company_data import firm_recycling_output_floor_gbp_m
from spatial_module import allocate_jobs, DISTRICTS


class CoupledModel:
    def __init__(self, name, policy, price_path=None, demand_growth=None,
                 start_year=2026, horizon=P.HORIZON, seed=0,
                 use_ree_pilot=False, adaptive=False, use_cge=False,
                 demand_plateau_years=None, import_constraint=None):
        self.name = name
        self.policy = policy
        # upstream supply shock: {mineral: max import as fraction of demand}.
        # A strategic stockpile / procurement reserve (Vision 2035 defence
        # resilience measure) raises the effective import availability during a
        # shock, buffering part of the lost supply. PROXY: full stockpile lever
        # offsets up to 0.30 of demand.
        stockpile = (policy or {}).get("strategic_stockpile", 0.0)
        self.import_constraint = {
            m: min(1.0, cap + 0.30 * stockpile)
            for m, cap in (import_constraint or {}).items()
        }
        self.start_year = start_year
        self.horizon = horizon
        self.seed = seed
        self.demand_growth = demand_growth or {}      # per-mineral annual demand growth
        # Years after which demand growth plateaus (e.g. 9 -> growth runs to 2035
        # then holds), so strong document-anchored CAGRs don't compound unrealistically.
        self.demand_plateau_years = demand_plateau_years
        self.price_path = price_path or {}            # per-mineral price index by year offset
        self.use_cge = use_cge
        self.io = DynamicIO()
        self.mfa = MFA(use_ree_pilot=use_ree_pilot)
        self.abm = MineralsABM(policy=policy, seed=seed, adaptive=adaptive)
        self.cge = None
        if use_cge:
            from cge_module import CGE
            self.cge = CGE()
        self.cge_feedback_price = 1.0     # CGE->ABM price feedback (Tier-3 loop)
        # Firm-grounded floor on recycling output (Ionic 400 tpa REE plant etc.):
        # the recycling sector cannot be smaller than the named NI plants imply.
        self.firm_recycling_floor = firm_recycling_output_floor_gbp_m(
            MINERAL_PRICE_GBP_PER_T, rows=self.abm.company_register)
        self.records = []

    def _price_index(self, t):
        return {m: (1.0 + self.price_path.get(m, 0.0)) ** t for m in P.MINERALS}

    def _demand_multiplier(self, t):
        company_signal = getattr(self.abm, "downstream_demand_signal", 1.0)
        teff = t if self.demand_plateau_years is None else min(t, self.demand_plateau_years)
        return {
            m: company_signal * (1.0 + self.demand_growth.get(m, 0.0)) ** teff
            for m in P.MINERALS
        }

    def _final_demand_vector(self, mfa_rows, ramp=1.0):
        """Convert physical flows to an I-O final-demand vector (£m). The
        recycling sector is floored at the named-plant capacity (ramped in over
        the horizon) so reported circular activity is grounded in real firms."""
        fd = np.zeros(P.N)
        for r in mfa_rows:
            price = MINERAL_PRICE_GBP_PER_T[r["mineral"]] / 1e6  # £m per tonne
            fd[P.S["Mining_Quarrying"]] += r["domestic_primary_t"] * price
            fd[P.S["Recycling_Secondary"]] += r["recycled_t"] * price
        rec = P.S["Recycling_Secondary"]
        fd[rec] = max(fd[rec], self.firm_recycling_floor * ramp)
        return fd

    def run(self):
        disc = 1.0
        cum = {"gva": 0.0, "jobs_years": 0.0, "co2": 0.0, "output": 0.0}
        for t in range(self.horizon):
            year = self.start_year + t
            # ABM sees exogenous price path x CGE price feedback (Tier-3 loop)
            pidx = self._price_index(t)
            pidx = {m: v * self.cge_feedback_price for m, v in pidx.items()}
            self.abm.price_index = pidx
            self.abm.step()
            sig = self.abm.signals

            mfa_rows = self.mfa.step(
                year,
                demand_multiplier=self._demand_multiplier(t),
                collection_boost=sig["collection_boost"],
                recovery_boost=sig["recovery_boost"],
                new_domestic=sig["new_domestic"],
                import_constraint=self.import_constraint,
            )
            sec = self.mfa.supply_security_summary(mfa_rows)
            sec_crit = self._critical_supply_summary(mfa_rows)

            # dynamic I-O coefficient evolution driven by ABM
            local_proc_gain = (
                self.policy.get("local_supplier_support", 0.0) * 0.05
                + sig.get("local_procurement_baseline", 0.0)
            )
            self.io.update_coefficients(
                recycling_substitution=min(0.05, sig["recycling_substitution"] * 0.05),
                local_procurement_gain=local_proc_gain,
                productivity_gain=0.005,
            )
            # plant ramp-up: floor reaches full installed capacity over ~5 years
            ramp = min(1.0, 0.4 + 0.12 * t)
            fd = self._final_demand_vector(mfa_rows, ramp=ramp)
            imp = self.io.impact(fd, induced=True)

            # --- Tier-3: CGE economy-wide adjustment + feedback to ABM ---
            cge_wage, cge_gva = np.nan, np.nan
            if self.use_cge:
                prod = np.ones(P.N)
                # recycling productivity rises with recovery capacity build-out
                rec_gain = np.mean(list(sig["recovery_boost"].values()) or [0.0])
                prod[P.S["Recycling_Secondary"]] = 1.0 + min(0.5, 3 * rec_gain)
                dem = np.ones(P.N)
                gd = (1 + np.mean(list(self.demand_growth.values()) or [0.0])) ** t
                dem[P.S["Manufacturing"]] = min(2.0, gd)
                sol = self.cge.solve({"productivity": prod, "demand_shift": dem})
                if sol["success"]:
                    cge_wage = sol["wage"]
                    cge_gva = sol["GVA"]
                    # feedback: relative mining price -> ABM mineral price next year
                    pd_mine = sol["PD"][P.S["Mining_Quarrying"]]
                    self.cge_feedback_price = float(np.clip(pd_mine, 0.8, 1.5))
                    # higher wage raises mining development hurdle (labour scarcity)
                    self.abm.dev_hurdle = 0.45 * (cge_wage if cge_wage > 0 else 1.0)

            # spatial allocation of jobs to council areas (Q2.5)
            jobs_by_district = allocate_jobs(imp["employment_by_sector"])

            disc = 1.0 / ((1.0 + P.STPR) ** t)
            cum["gva"] += imp["gva_total"] * disc
            cum["jobs_years"] += imp["employment_total"] * disc
            cum["co2"] += imp["co2_total"] * disc
            cum["output"] += imp["output_total"] * disc

            self.records.append({
                "scenario": self.name, "year": year,
                "mining_fd_gbp_m": fd[P.S["Mining_Quarrying"]],
                "recycling_fd_gbp_m": fd[P.S["Recycling_Secondary"]],
                "output_total_gbp_m": imp["output_total"],
                "gva_total_gbp_m": imp["gva_total"],
                "employment_total": imp["employment_total"],
                "recycling_jobs": imp["employment_by_sector"][P.S["Recycling_Secondary"]],
                "mining_jobs": imp["employment_by_sector"][P.S["Mining_Quarrying"]],
                "manufacturing_jobs": imp["employment_by_sector"][P.S["Manufacturing"]],
                "co2_kt": imp["co2_total"],
                "pm_t": imp["pm_total"],
                "mines_opened": sig["mines_opened_cumulative"],
                "crit_recycled_share": sec_crit["recycled_share"],
                "crit_domestic_share": sec_crit["domestic_share"],
                "crit_import_share": sec_crit["import_share"],
                "crit_supply_gap": sec_crit["supply_gap_share"],
                "crit_max_single_country": sec_crit["max_single_country_exposure"],
                "recycled_share_all": sec["recycled_share"],
                "recycling_substitution": sig.get("recycling_substitution", 0.0),
                **sig.get("company_context", {}),
                "cge_wage_index": cge_wage,
                "cge_gva_total_gbp_m": cge_gva,
                **{f"jobs_{d}": j for d, j in jobs_by_district.items()},
            })
        self.cumulative_discounted = cum
        return pd.DataFrame(self.records)

    def _critical_supply_summary(self, mfa_rows):
        crit = [r for r in mfa_rows if r["mineral"] in P.CRITICAL_MINERALS]
        tot = sum(r["demand_t"] for r in crit) or 1.0
        return {
            "recycled_share": sum(r["recycled_t"] for r in crit) / tot,
            "domestic_share": sum(r["domestic_primary_t"] for r in crit) / tot,
            "import_share": sum(r["imports_t"] for r in crit) / tot,
            "supply_gap_share": sum(r.get("unmet_demand_t", 0.0) for r in crit) / tot,
            "max_single_country_exposure": max(r["single_country_exposure"] for r in crit),
        }
