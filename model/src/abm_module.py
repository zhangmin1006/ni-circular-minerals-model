"""
Agent-Based Model: NI minerals supply-chain & circular-economy engine.

Tier-1 (MVM) = rule-based agents (no learning yet; that is Tier 2). Built on
mesa 3.x. Each simulated year the agents make decisions that change the physical
system (the MFA) and the economic demand vector (fed to the dynamic I-O):

  MiningFirm        : real-option decision to develop a deposit -> domestic primary
  RecyclerFirm      : invest in recovery capacity -> collection/recovery boosts
  Manufacturer      : substitute secondary for primary material -> I-O coefficient shift
  CouncilCollector  : raise collection rates under circular-economy policy

The Government/policy levers are passed in via a `policy` dict (the scenario layer).
Behavioural parameters (thresholds, costs) are PROXY — see data_register.csv.
"""

import numpy as np
import mesa
import seed_parameters as P
from mfa_module import MINERAL_PARAMS
from company_data import (
    company_context,
    downstream_demand_signal,
    load_company_register,
    local_procurement_baseline,
    mineral_project_properties,
    recycler_capacity_by_mineral,
    recycler_focus_minerals,
)


class MiningFirm(mesa.Agent):
    """Decides whether to develop a deposit using a simple real-option trigger:
    develop only if expected NPV margin clears the hurdle set by cost of equity,
    permitting delay, ESG cost and social-licence acceptance."""

    def __init__(self, model, mineral, deposit_quality, project_risk=0.3,
                 output_share_potential=None):
        super().__init__(model)
        self.mineral = mineral
        self.deposit_quality = deposit_quality      # 0-1, from Tellus/geology proxy
        self.project_risk = project_risk            # planning/social/enviro risk, 0-1
        self.developed = False
        self.years_in_permitting = 0
        self.output_share = 0.0                      # share of NI demand it can supply
        self.output_share_potential = output_share_potential
        self.expected_price = 1.0                    # adaptive price expectation

    def step(self):
        if self.developed:
            return
        pol = self.model.policy
        observed_price = self.model.price_index.get(self.mineral, 1.0)
        if self.model.adaptive:
            # adaptive expectations: blend last expectation with observed price
            lam = self.model.expectation_weight
            self.expected_price = lam * observed_price + (1 - lam) * self.expected_price
            price_signal = self.expected_price
        else:
            price_signal = observed_price
        # expected margin: better deposits + higher prices + grants raise it;
        # ESG cost + weak social licence + high cost of equity lower it.
        margin = (self.deposit_quality * price_signal
                  + pol.get("exploration_grant", 0.0)
                  - pol.get("esg_cost", 0.10)
                  - 0.12 * self.project_risk
                  - P.MINING_COST_OF_EQUITY)
        social_licence = (self.model.social_licence
                          - pol.get("esg_cost", 0.0) * 0.5
                          - 0.25 * self.project_risk)

        if margin > self.model.dev_hurdle and social_licence > 0.4:
            self.years_in_permitting += 1
            permit_years = max(1, pol.get("permit_years", 3))
            if self.years_in_permitting >= permit_years:
                self.developed = True
                # a developed deposit supplies a share of NI demand for that mineral
                self.output_share = self.output_share_potential or (0.15 * self.deposit_quality)
                self.model.new_domestic[self.mineral] = (
                    self.model.new_domestic.get(self.mineral, 0.0) + self.output_share)
                self.model.mines_opened += 1


class RecyclerFirm(mesa.Agent):
    """Invests in recovery capacity for a mineral when circular policy support and
    secondary-material price make it viable -> boosts recovery yield & collection."""

    def __init__(self, model, mineral, capacity_signal=0.5):
        super().__init__(model)
        self.mineral = mineral
        self.capacity = 0.0
        self.capacity_signal = capacity_signal

    def step(self):
        pol = self.model.policy
        support = (pol.get("recycling_grant", 0.0)
                   + pol.get("recycled_content_procurement", 0.0)
                   + self.model.price_index.get(self.mineral, 1.0) - 1.0)
        energy_penalty = pol.get("energy_cost_index", 1.0) - 1.0
        viability = support - 0.3 * energy_penalty
        viability += 0.08 * (self.capacity_signal - 0.5)
        # adaptive imitation: if peers are expanding faster, raise own propensity
        if self.model.adaptive:
            peer_cap = self.model.mean_recycler_capacity
            if peer_cap > self.capacity:
                viability += 0.05 * self.model.imitation_strength
        if viability > 0.05:
            gain = min(0.05, 0.06 * viability * (0.75 + self.capacity_signal))
            self.capacity += gain
            self.model.recovery_boost[self.mineral] = min(
                0.30, self.model.recovery_boost.get(self.mineral, 0.0) + gain)


class CouncilCollector(mesa.Agent):
    """Raises collection rates for WEEE/batteries/ELV under circular policy
    (better infrastructure, deposit-return, product stewardship)."""

    def __init__(self, model):
        super().__init__(model)

    def step(self):
        pol = self.model.policy
        drive = (pol.get("collection_infrastructure", 0.0)
                 + pol.get("product_passport", 0.0))
        if drive > 0:
            for m in P.CRITICAL_MINERALS:
                self.model.collection_boost[m] = min(
                    0.50, self.model.collection_boost.get(m, 0.0) + 0.03 * drive)


class Manufacturer(mesa.Agent):
    """Substitutes secondary for primary material when secondary supply grows and
    design-for-disassembly / recycled-content standards apply. Drives the I-O
    coefficient shift (mining -> recycling)."""

    def __init__(self, model):
        super().__init__(model)
        self.secondary_uptake = 0.0

    def step(self):
        pol = self.model.policy
        avail = np.mean([self.model.recovery_boost.get(m, 0.0)
                         for m in P.CRITICAL_MINERALS])
        push = pol.get("design_standards", 0.0) + pol.get("recycled_content_procurement", 0.0)
        self.secondary_uptake = min(0.6, self.secondary_uptake + 0.5 * avail + 0.05 * push)
        self.model.recycling_substitution = self.secondary_uptake


class MineralsABM(mesa.Model):
    """Tier-1 rule-based supply-chain model for one year-step."""

    def __init__(self, policy=None, price_index=None, seed=None,
                 adaptive=False, expectation_weight=0.5, imitation_strength=1.0):
        super().__init__(seed=seed)
        self.policy = policy or {}
        self.price_index = price_index or {m: 1.0 for m in P.MINERALS}
        self.company_register = load_company_register()
        self.company_context = company_context(self.company_register)
        self.local_procurement_baseline = local_procurement_baseline(self.company_register)
        self.downstream_demand_signal = downstream_demand_signal(self.company_register)
        # Tier-2 behavioural switches
        self.adaptive = adaptive
        self.expectation_weight = expectation_weight   # adaptive-expectations weight
        self.imitation_strength = imitation_strength
        self.mean_recycler_capacity = 0.0
        self.social_licence = 0.6
        # development hurdle set so baseline opens only the most favourable (bulk)
        # deposits; grants / higher prices are needed to bring critical-mineral
        # deposits forward. PROXY.
        self.dev_hurdle = 0.45
        self.mines_opened = 0

        # signals the ABM emits to MFA / I-O each step (reset annually)
        self.new_domestic = {}
        self.recovery_boost = {}
        self.collection_boost = {}
        self.recycling_substitution = 0.0

        # Populate agents from the web-verified company evidence layer, with the
        # original Minviro-style proxy set retained as a fallback.
        deposits = {
            "Antimony": {"deposit_quality": 0.6, "project_risk": 0.55, "output_share": 0.10},
            "Baryte": {"deposit_quality": 0.7, "project_risk": 0.35, "output_share": 0.12},
            "Aluminium": {"deposit_quality": 0.5, "project_risk": 0.35, "output_share": 0.08},
            "Copper": {"deposit_quality": 0.55, "project_risk": 0.45, "output_share": 0.09},
            "Salt": {"deposit_quality": 0.9, "project_risk": 0.20, "output_share": 0.16},
        }
        deposits.update(mineral_project_properties(self.company_register))
        for mineral, props in deposits.items():
            MiningFirm(
                self,
                mineral,
                props["deposit_quality"],
                project_risk=props.get("project_risk", 0.35),
                output_share_potential=props.get("output_share"),
            )

        recycler_minerals = recycler_focus_minerals(self.company_register) or P.CRITICAL_MINERALS
        recycler_capacity = recycler_capacity_by_mineral(self.company_register)
        for mineral in recycler_minerals:
            RecyclerFirm(self, mineral, recycler_capacity.get(mineral, 0.5))
        CouncilCollector(self)
        Manufacturer(self)

    def step(self):
        # reset annual signals (mines persist via new_domestic accumulation in coupling)
        self.recovery_boost = {}
        self.collection_boost = {}
        self.recycling_substitution = 0.0
        # update peer benchmark for imitation (Tier-2 adaptive behaviour)
        recyclers = self.agents_by_type.get(RecyclerFirm, [])
        if recyclers:
            self.mean_recycler_capacity = np.mean([a.capacity for a in recyclers])
        # decision order: councils & recyclers first (supply), then manufacturers, then mines
        for cls in (CouncilCollector, RecyclerFirm, Manufacturer, MiningFirm):
            for a in self.agents_by_type.get(cls, []):
                a.step()
        # mesa 3.x wraps step() and discards its return value, so publish signals
        # as an attribute for the coupling layer to read.
        self.signals = {
            "mines_opened_cumulative": self.mines_opened,
            "new_domestic": dict(self.new_domestic),
            "recovery_boost": dict(self.recovery_boost),
            "collection_boost": dict(self.collection_boost),
            "recycling_substitution": self.recycling_substitution,
            "company_context": dict(self.company_context),
            "local_procurement_baseline": self.local_procurement_baseline,
            "downstream_demand_signal": self.downstream_demand_signal,
        }
        return self.signals


if __name__ == "__main__":
    pol = {"recycling_grant": 0.3, "collection_infrastructure": 1.0,
           "design_standards": 0.5, "exploration_grant": 0.15, "permit_years": 3}
    m = MineralsABM(policy=pol, seed=42)
    for yr in range(2026, 2031):
        m.step()
        out = m.signals
        print(yr, "mines:", out["mines_opened_cumulative"],
              "recyc_sub: %.3f" % out["recycling_substitution"],
              "collect_boost_minerals:", len(out["collection_boost"]))
