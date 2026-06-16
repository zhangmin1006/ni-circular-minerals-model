"""
Agent-Based Model: NI minerals supply-chain & circular-economy engine.

REDESIGNED to be firm-grounded: every agent is a NAMED Northern Ireland operator
read from data/company_register.csv (via company_data.parse_firms). Each firm's
behaviour is driven by its own evidence-based attributes — lifecycle stage,
deposit/feedstock/circularity scores, planning-risk (social licence), employees,
installed plant capacity and district — instead of one abstract agent per mineral.

Agent types (all heterogeneous, one instance per real firm):

  MiningFirm        : Dalradian, Conroy, Galantas, Irish Salt, Kilwaughter, FP
                      McCann, Mannok, Breedon ... A real-option development trigger
                      decides whether a *proposed/exploration* project is built;
                      *operating* quarries/mines already supply. Contested deposits
                      (high planning-risk -> weak social licence) can stay blocked
                      even when economics clear, reproducing NI's permitting reality.
  RecyclerFirm      : processors (Ionic -> REE recovery capacity) and feedstock
                      collectors (Re-Gen, RiverRidge, Bryson, Envirogreen -> WEEE/
                      ELV/battery collection). Installed plant gives a head start.
  ManufacturerFirm  : downstream demand + recycled-content uptake (Wrightbus,
                      Seagate, Encirc, Spirit, H&W) and equipment supply-chain
                      enablers (CDE, Terex) that make recycler capacity cheaper.
  GovernmentCollector: policy-driven municipal collection across critical minerals.

For tracked minerals with NO named operator but plausible NI geology (Baryte,
Aluminium) a small number of clearly-labelled "geological-potential" proxy mining
agents are added so the option space is not silently empty.

The model still publishes the same `signals` dict (new_domestic, recovery_boost,
collection_boost, recycling_substitution, company context ...) that the coupling
layer reads, so the MFA / I-O / CGE pipeline and the Minviro validation are
unchanged. Behavioural thresholds remain PROXY — see data_register.csv.
"""

import math

import numpy as np
import mesa
import seed_parameters as P
from company_data import (
    DOWNSTREAM_ROLES,
    MINING_ROLES,
    RECYCLING_ROLES,
    company_context,
    downstream_demand_signal,
    load_company_register,
    local_procurement_baseline,
    parse_firms,
)

# Geological-potential proxies used ONLY for tracked minerals that no named firm
# covers (NI has no primary REE/Li/Co/Ni operators, so those stay recycling-only).
PROXY_DEPOSITS = {
    "Baryte": {"resource": 0.75, "capacity": 0.60, "planning_risk": 0.35,
               "local_procurement": 0.35},
    "Aluminium": {"resource": 0.50, "capacity": 0.45, "planning_risk": 0.35,
                  "local_procurement": 0.35},
}

SOCIAL_LICENCE_FLOOR = 0.4   # below this a project cannot proceed regardless of NPV


class Firm(mesa.Agent):
    """Base for every named-firm agent; carries the parsed register record."""

    def __init__(self, model, rec):
        super().__init__(model)
        self.rec = rec
        self.name = rec["name"]
        self.district = rec["district"]
        self.s = rec["scores"]


class MiningFirm(Firm):
    """A named mine/quarry (or a geological-potential proxy). Operating sites
    supply their tracked minerals immediately; proposed/exploration projects must
    clear a real-option NPV hurdle AND a social-licence floor before developing."""

    def __init__(self, model, rec, proxy=False):
        super().__init__(model, rec)
        self.proxy = proxy
        self.minerals = sorted(rec["minerals"])          # tracked minerals supplied
        s = self.s
        self.deposit_quality = float(np.clip(
            (0.65 * s["resource"] + 0.35 * s["capacity"]) * rec["confidence"], 0.0, 1.0))
        self.project_risk = s["planning_risk"]           # planning/social/enviro risk
        self.output_share = round(min(0.18, max(0.03, 0.05 + 0.13 * s["capacity"])), 3)
        self.expected_price = 1.0
        self.years_in_permitting = 0
        # operating assets are already producing; everything else awaits a decision
        self.developed = rec["lifecycle"] == "operating"
        self.newly_opened = False
        self._contributed = False

    def _supply(self):
        for m in self.minerals:
            self.model.new_domestic[m] = self.model.new_domestic.get(m, 0.0) + self.output_share
        self._contributed = True

    def step(self):
        if self.developed:
            # ensure an operating/just-developed mine's output is registered once
            if self.minerals and not self._contributed:
                self._supply()
            return
        if not self.minerals:
            return  # exploration with no tracked critical mineral -> context only

        pol = self.model.policy
        observed = float(np.mean([self.model.price_index.get(m, 1.0) for m in self.minerals]))
        if self.model.adaptive:
            lam = self.model.expectation_weight
            self.expected_price = lam * observed + (1 - lam) * self.expected_price
            price_signal = self.expected_price
        else:
            price_signal = observed

        # Q2.2 constraint levers: finance support cuts the effective cost of
        # capital (National Wealth Fund / UKEF co-investment & guarantees);
        # community benefit raises social licence; skills availability eases the
        # hurdle and shortens permitting (labour/expertise to deliver).
        finance = pol.get("finance_support", 0.0)
        community = pol.get("community_benefit", 0.0)
        skills = pol.get("skills_support", 0.0)
        eff_wacc = P.MINING_COST_OF_EQUITY * (1.0 - 0.5 * finance)

        margin = (self.deposit_quality * price_signal
                  + pol.get("exploration_grant", 0.0)
                  + 0.05 * skills
                  - pol.get("esg_cost", 0.10)
                  - 0.12 * self.project_risk
                  - eff_wacc)
        social_licence = (self.model.social_licence
                          - pol.get("esg_cost", 0.0) * 0.5
                          - 0.25 * self.project_risk
                          + 0.30 * community)

        if margin > self.model.dev_hurdle and social_licence > SOCIAL_LICENCE_FLOOR:
            self.years_in_permitting += 1
            # contested projects take longer to permit; skills availability and
            # permitting reform shorten the (risk-extended) delay.
            permit_years = (max(1, pol.get("permit_years", 3))
                            + int(round(3 * self.project_risk * (1.0 - 0.5 * skills))))
            if self.years_in_permitting >= permit_years:
                self.developed = True
                self.newly_opened = True
                self._supply()
                self.model.mines_opened += 1
        else:
            self.years_in_permitting = 0   # stalled projects lose momentum


class RecyclerFirm(Firm):
    """Processor (recovers metal -> recovery_boost) or feedstock collector (raises
    collection rates -> collection_boost), per the firm's role and feedstock tags."""

    def __init__(self, model, rec):
        super().__init__(model, rec)
        self.processor = rec["role"] == "critical_mineral_recycler"
        self.targets = sorted(rec["recycler_targets"])
        self.capacity = 0.0
        s = self.s
        self.capacity_signal = 0.55 * s["capacity"] + 0.45 * s["feedstock"]
        self.feedstock_strength = s["feedstock"] * rec["confidence"]
        self.has_plant = rec["capacity_tonnes"] > 0      # e.g. Ionic 400 tpa

    def step(self):
        pol = self.model.policy
        innovation = pol.get("innovation_grant", 0.0)        # R&D co-funding
        skills = pol.get("skills_support", 0.0)              # green-skills/cluster
        market = pol.get("secondary_market_support", 0.0)    # offtake/marketplace
        if self.processor:
            support = (pol.get("recycling_grant", 0.0)
                       + pol.get("recycled_content_procurement", 0.0)
                       + 0.5 * market                        # offtake certainty de-risks capex
                       + float(np.mean([self.model.price_index.get(m, 1.0)
                                        for m in self.targets] or [1.0])) - 1.0)
            energy_penalty = pol.get("energy_cost_index", 1.0) - 1.0
            viability = support - 0.3 * energy_penalty
            viability += 0.08 * (self.capacity_signal - 0.5)
            viability += 0.04 * self.model.equipment_support     # CDE/Terex enable capex
            viability += 0.15 * innovation                       # R&D lowers process risk/cost
            if self.has_plant:
                viability += 0.05                                # plant already commissioned
            if self.model.adaptive and self.model.mean_recycler_capacity > self.capacity:
                viability += 0.05 * self.model.imitation_strength
            if viability > 0.05:
                # skills funding speeds the build-out of recovery capacity
                gain = min(0.06, 0.06 * viability * (0.75 + self.capacity_signal)
                           * (1.0 + 0.3 * skills))
                self.capacity += gain
                for m in self.targets:
                    bump = gain if m in P.CRITICAL_MINERALS else 0.5 * gain
                    # process innovation lifts achievable recovery yield directly
                    bump += 0.02 * innovation * (1.0 if m in P.CRITICAL_MINERALS else 0.5)
                    self.model.recovery_boost[m] = min(
                        0.35, self.model.recovery_boost.get(m, 0.0) + bump)
        else:
            # waste recyclers collect even with no policy (a small autonomous rate
            # set by feedstock strength), and respond to collection/passport policy.
            drive = pol.get("collection_infrastructure", 0.0) + pol.get("product_passport", 0.0)
            add = 0.008 * self.feedstock_strength + 0.02 * drive * (0.5 + self.feedstock_strength)
            if add > 0:
                for m in self.targets:
                    self.model.collection_boost[m] = min(
                        0.50, self.model.collection_boost.get(m, 0.0) + add)


class ManufacturerFirm(Firm):
    """Downstream demand + recycled-content uptake (drives the I-O mining->recycling
    coefficient shift), or an equipment supply-chain enabler for recyclers/miners."""

    def __init__(self, model, rec):
        super().__init__(model, rec)
        self.downstream = rec["role"] == "downstream_manufacturer"
        s = self.s
        self.demand = s["demand"]
        self.circularity = s["circularity"]
        self.weight = math.log1p(max(0.0, rec["employees"]))
        self.uptake = 0.0

    def step(self):
        if not self.downstream:
            return  # supply-chain enablers act via model.equipment_support (static)
        pol = self.model.policy
        innovation = pol.get("innovation_grant", 0.0)
        skills = pol.get("skills_support", 0.0)
        market = pol.get("secondary_market_support", 0.0)
        avail = float(np.mean([self.model.recovery_boost.get(m, 0.0)
                               for m in P.CRITICAL_MINERALS]))
        push = pol.get("design_standards", 0.0) + pol.get("recycled_content_procurement", 0.0)
        # circular-design R&D / passports let a firm exceed its baseline circularity
        ceiling = min(0.85, self.circularity + 0.15 * innovation + 0.05 * market)
        rate = (0.5 * avail * self.circularity
                + 0.05 * push * self.circularity
                + 0.04 * innovation * self.circularity   # design-for-disassembly R&D
                + 0.03 * skills * self.circularity        # design/process skills
                + 0.05 * market * self.circularity)       # trusted secondary supply
        self.uptake = min(ceiling, self.uptake + rate)


class GovernmentCollector(mesa.Agent):
    """Policy lever: municipal collection infrastructure / product passports lift
    collection rates for all critical minerals (on top of firm-level collection)."""

    def __init__(self, model):
        super().__init__(model)

    def step(self):
        pol = self.model.policy
        drive = pol.get("collection_infrastructure", 0.0) + pol.get("product_passport", 0.0)
        if drive > 0:
            for m in P.CRITICAL_MINERALS:
                self.model.collection_boost[m] = min(
                    0.50, self.model.collection_boost.get(m, 0.0) + 0.03 * drive)


class MineralsABM(mesa.Model):
    """Tier-1 rule-based, firm-grounded supply-chain model for one year-step."""

    def __init__(self, policy=None, price_index=None, seed=None,
                 adaptive=False, expectation_weight=0.5, imitation_strength=1.0):
        super().__init__(seed=seed)
        self.policy = policy or {}
        self.price_index = price_index or {m: 1.0 for m in P.MINERALS}
        self.company_register = load_company_register()
        firms = parse_firms(self.company_register)

        # aggregate evidence signals (unchanged interface for the coupling layer)
        self.company_context = company_context(self.company_register)
        self.local_procurement_baseline = local_procurement_baseline(self.company_register)
        self.downstream_demand_signal = downstream_demand_signal(self.company_register)

        # Tier-2 behavioural switches
        self.adaptive = adaptive
        self.expectation_weight = expectation_weight
        self.imitation_strength = imitation_strength
        self.mean_recycler_capacity = 0.0
        self.social_licence = 0.6
        self.dev_hurdle = 0.45                 # PROXY development hurdle
        self.mines_opened = 0

        # signals emitted to MFA / I-O each step
        self.new_domestic = {}                 # persists across years (mines stay open)
        self.recovery_boost = {}
        self.collection_boost = {}
        self.recycling_substitution = 0.0

        # instantiate one agent per named firm
        self._manufacturers = []
        self._processors = []
        covered_minerals = set()
        for rec in firms:
            role = rec["role"]
            if role in MINING_ROLES:
                MiningFirm(self, rec)
                covered_minerals |= rec["minerals"]
            elif role in RECYCLING_ROLES:
                r = RecyclerFirm(self, rec)
                if r.processor:
                    self._processors.append(r)
            elif role in DOWNSTREAM_ROLES:
                m = ManufacturerFirm(self, rec)
                if m.downstream:
                    self._manufacturers.append(m)

        # geological-potential proxies only where no named operator exists
        for mineral, props in PROXY_DEPOSITS.items():
            if mineral not in covered_minerals:
                MiningFirm(self, self._proxy_record(mineral, props), proxy=True)

        GovernmentCollector(self)

        # static supply-chain enabler strength from equipment makers (CDE, Terex)
        self.equipment_support = self._equipment_support(firms)

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _proxy_record(mineral, props):
        scores = {"resource": props["resource"], "capacity": props["capacity"],
                  "feedstock": 0.5, "demand": 0.5,
                  "local_procurement": props["local_procurement"],
                  "planning_risk": props["planning_risk"],
                  "skills_intensity": 0.5, "circularity": 0.2}
        return {"name": f"[geological-potential] {mineral}", "role": "mining_exploration",
                "sector": "Mining_Quarrying", "district": "", "lifecycle": "proposed",
                "products": {mineral}, "minerals": {mineral}, "recycler_targets": set(),
                "employees": 0.0, "investment_gbp_m": 0.0, "capacity_tonnes": 0.0,
                "confidence": 0.85, "scores": scores}   # GSNI Tellus geochemical evidence

    @staticmethod
    def _equipment_support(firms):
        eq = [f for f in firms if f["role"] == "supply_chain_manufacturer"]
        if not eq:
            return 0.0
        num = sum(f["scores"]["demand"] * math.log1p(max(0.0, f["employees"])) for f in eq)
        den = sum(math.log1p(max(0.0, f["employees"])) for f in eq) or 1.0
        return round(0.3 * num / den, 4)

    def _aggregate_substitution(self):
        if not self._manufacturers:
            return 0.0
        num = sum(m.uptake * m.weight for m in self._manufacturers)
        den = sum(m.weight for m in self._manufacturers) or 1.0
        return num / den

    # -- step ---------------------------------------------------------------
    def step(self):
        # reset annual flow signals (new_domestic persists: opened mines stay open)
        self.recovery_boost = {}
        self.collection_boost = {}
        if self._processors:
            self.mean_recycler_capacity = float(np.mean([p.capacity for p in self._processors]))

        # decision order: collection/recovery supply first, then demand-side
        # substitution, then mining development decisions.
        for cls in (GovernmentCollector, RecyclerFirm, ManufacturerFirm, MiningFirm):
            for a in self.agents_by_type.get(cls, []):
                a.step()

        self.recycling_substitution = self._aggregate_substitution()

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
    pol = {"recycling_grant": 0.4, "collection_infrastructure": 1.0,
           "design_standards": 0.6, "exploration_grant": 0.18, "esg_cost": 0.08,
           "permit_years": 3}
    m = MineralsABM(policy=pol, seed=42)
    print(f"agents: {len(m.agents)} | equipment_support={m.equipment_support}")
    for yr in range(2026, 2041):
        m.step()
        out = m.signals
        if yr % 3 == 0 or out["mines_opened_cumulative"]:
            print(yr, "mines_opened:", out["mines_opened_cumulative"],
                  "| recyc_sub: %.3f" % out["recycling_substitution"],
                  "| recovery_minerals:", sorted(out["recovery_boost"]),
                  "| domestic:", {k: round(v, 2) for k, v in out["new_domestic"].items()})
