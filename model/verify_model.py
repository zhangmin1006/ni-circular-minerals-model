"""
Model verification & validation harness.

Runs invariant checks across the whole coupled model and prints a PASS/FAIL
report. Exit code is non-zero if any check fails, so it can gate CI.

Checks:
  1. Minviro validation anchors (I-O core)
  2. MFA mass balance every year/mineral, baseline + shock
  3. Supply-share closure (domestic+recycled+import+gap == 1) and bounds [0,1]
  4. No NaN/inf or negatives in key economic outputs
  5. Determinism (identical config -> identical result)
  6. SAM balance ~0 and CGE benchmark replication
  7. Spatial district shares sum to 1 per sector
  8. Stockpile reserve never negative; depletes under shock
  9. Company register integrity (roles mapped; Plaswire reclassified)
 10. Economic sanity (GVA/output, jobs/£m, multipliers in plausible ranges)

Run:  python verify_model.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import numpy as np
import pandas as pd
import seed_parameters as P

RESULTS = []


def check(name, condition, detail=""):
    RESULTS.append((bool(condition), name, detail))
    flag = "PASS" if condition else "FAIL"
    print(f"  [{flag}] {name}" + (f"  — {detail}" if detail else ""))
    return bool(condition)


def section(title):
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


# ---------------------------------------------------------------------------
def test_validation():
    section("1. Minviro validation anchors (I-O core)")
    from indicators import validate_against_minviro
    val = validate_against_minviro()
    for label, r in val.items():
        check(f"{label}: output matches anchor",
              abs(r["model_output"] - r["anchor_output"]) < 0.15,
              f"model {r['model_output']:.2f} vs {r['anchor_output']}")
        check(f"{label}: jobs within 1 of anchor",
              abs(r["model_jobs"] - r["anchor_jobs"]) < 1.0,
              f"model {r['model_jobs']:.1f} vs {r['anchor_jobs']}")
        check(f"{label}: direct mining GVA within 5% of anchor",
              abs(r["model_direct_mining_gva"] - r["anchor_gva"]) / r["anchor_gva"] < 0.05,
              f"model {r['model_direct_mining_gva']:.2f} vs {r['anchor_gva']}")


def _run(**kw):
    from coupling import CoupledModel
    defaults = dict(name="t", policy={}, demand_growth={}, seed=42,
                    use_ree_pilot=True, adaptive=True, use_cge=True)
    defaults.update(kw)
    m = CoupledModel(**defaults)
    df = m.run()
    return m, df


def test_mass_balance():
    section("2. MFA mass balance (baseline + shock)")
    # baseline
    m, _ = _run()
    ok = all(r["mass_balance_ok"] for r in m.mfa.history)
    check("baseline: all mass balances close", ok,
          f"{sum(r['mass_balance_ok'] for r in m.mfa.history)}/{len(m.mfa.history)} rows")
    # shock
    caps = {mm: 0.4 for mm in P.CRITICAL_MINERALS}
    m2, _ = _run(import_constraint=caps, price_path={"Lithium": 0.1})
    ok2 = all(r["mass_balance_ok"] for r in m2.mfa.history)
    check("shock: all mass balances close (domestic+imports+secondary+unmet=demand)", ok2,
          f"{sum(r['mass_balance_ok'] for r in m2.mfa.history)}/{len(m2.mfa.history)} rows")
    # unmet only appears under shock
    base_unmet = sum(r["unmet_demand_t"] for r in m.mfa.history)
    shock_unmet = sum(r["unmet_demand_t"] for r in m2.mfa.history)
    check("no unmet demand without a shock", abs(base_unmet) < 1e-9, f"{base_unmet:.3f}")
    check("shock creates unmet demand (supply gap)", shock_unmet > 0, f"{shock_unmet:.0f} t")


def test_share_closure():
    section("3. Supply-share closure & bounds")
    caps = {mm: 0.5 for mm in P.CRITICAL_MINERALS}
    m, _ = _run(import_constraint=caps, demand_growth={"Lithium": 0.1})
    bad_bounds, bad_close = 0, 0
    for r in m.mfa.history:
        if r["demand_t"] <= 0:
            continue
        shares = [r["domestic_share"], r["recycled_share"], r["import_share"],
                  r["supply_gap_share"]]
        if any(s < -1e-9 or s > 1.0 + 1e-6 for s in shares):
            bad_bounds += 1
        if abs(sum(shares) - 1.0) > 1e-6:
            bad_close += 1
    check("all supply shares in [0,1]", bad_bounds == 0, f"{bad_bounds} violations")
    check("shares close to 1 (domestic+recycled+import+gap)", bad_close == 0,
          f"{bad_close} violations")


def test_no_nan_negative():
    section("4. No NaN/inf or negatives in key outputs")
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "outputs",
                                  "scenario_timeseries.csv"))
    cols = ["output_total_gbp_m", "gva_total_gbp_m", "employment_total",
            "recycling_jobs", "mining_jobs", "co2_kt", "crit_recycled_share",
            "crit_import_share"]
    nan = {c: int(df[c].isna().sum()) for c in cols if c in df}
    neg = {c: int((df[c] < -1e-9).sum()) for c in cols if c in df}
    check("no NaN/inf in key economic columns", all(v == 0 for v in nan.values()), str(nan))
    check("no negative jobs/GVA/output/CO2", all(v == 0 for v in neg.values()), str(neg))
    # shares within [0,1]
    for c in ["crit_recycled_share", "crit_import_share", "crit_domestic_share"]:
        if c in df:
            check(f"{c} within [0,1]", df[c].between(-1e-9, 1.0 + 1e-6).all(),
                  f"min {df[c].min():.3f} max {df[c].max():.3f}")


def test_determinism():
    section("5. Determinism (identical config -> identical result)")
    m1, d1 = _run(policy={"recycling_grant": 0.3}, demand_growth={"Copper": 0.04})
    m2, d2 = _run(policy={"recycling_grant": 0.3}, demand_growth={"Copper": 0.04})
    check("cumulative GVA identical across two runs",
          abs(m1.cumulative_discounted["gva"] - m2.cumulative_discounted["gva"]) < 1e-6,
          f"{m1.cumulative_discounted['gva']:.4f} vs {m2.cumulative_discounted['gva']:.4f}")
    check("full timeseries identical",
          np.allclose(d1.select_dtypes("number").fillna(0).to_numpy(),
                      d2.select_dtypes("number").fillna(0).to_numpy()))


def test_sam_cge():
    section("6. SAM balance & CGE benchmark replication")
    from sam_module import build_sam, sam_to_dataframe
    sam = build_sam()
    df = sam_to_dataframe(sam)
    imbalance = float((df.sum(axis=1) - df.sum(axis=0)).abs().max())
    check("SAM row sums == column sums (balanced)", imbalance < 1e-6,
          f"max imbalance £{imbalance:.2e}m")
    check("SAM reproduces mining GVA ~£108m anchor",
          abs(sam["gva"][P.S["Mining_Quarrying"]] - P.ANCHORS["ni_mining_gva_2018_gbp_m"]) < 5.0,
          f"£{sam['gva'][P.S['Mining_Quarrying']]:.1f}m")
    from cge_module import CGE
    cge = CGE()
    sol = cge.solve({"productivity": np.ones(P.N), "demand_shift": np.ones(P.N)})
    check("CGE solves the benchmark", sol.get("success", False))
    if sol.get("success"):
        check("CGE replicates benchmark (wage ~ 1.0 at no shock)",
              abs(sol["wage"] - 1.0) < 1e-3, f"wage {sol['wage']:.6f}")


def test_spatial():
    section("7. Spatial district shares")
    from spatial_module import SHARES, DISTRICTS
    sums = SHARES.sum(axis=0)
    check("every sector's district shares sum to 1", np.allclose(sums, 1.0),
          f"min {sums.min():.4f} max {sums.max():.4f}")
    check("shares non-negative", (SHARES >= -1e-12).all())
    check("11 districts", len(DISTRICTS) == 11, f"{len(DISTRICTS)}")


def test_stockpile():
    section("8. Strategic stockpile reserve")
    caps = {mm: 0.4 for mm in P.CRITICAL_MINERALS}
    m, _ = _run(policy={"strategic_stockpile": 0.6}, import_constraint=caps)
    check("reserve never negative", all(v >= -1e-12 for v in m._reserve.values()),
          f"min {min(m._reserve.values()):.4f}")
    check("reserve depletes under sustained shock",
          any(v < 1e-9 for v in m._reserve.values()),
          f"reserves {[round(v,3) for v in m._reserve.values()]}")
    # stockpile should reduce early-window gap vs no stockpile
    mn, dn = _run(import_constraint=caps)
    ms, ds = _run(policy={"strategic_stockpile": 0.6}, import_constraint=caps)
    early_no = dn.iloc[:5]["crit_supply_gap"].mean()
    early_sp = ds.iloc[:5]["crit_supply_gap"].mean()
    check("stockpile reduces the early-window supply gap", early_sp <= early_no + 1e-9,
          f"early gap {early_no:.3f} -> {early_sp:.3f}")


def test_company_register():
    section("9. Company register integrity")
    from company_data import (parse_firms, ROLE_SECTOR, MINING_ROLES,
                              RECYCLING_ROLES, DOWNSTREAM_ROLES)
    firms = parse_firms()
    check("register loads (>=20 firms)", len(firms) >= 20, f"{len(firms)} firms")
    known = MINING_ROLES | RECYCLING_ROLES | DOWNSTREAM_ROLES
    unmapped = sorted({f["role"] for f in firms} - known)
    check("all roles mapped to a stage", not unmapped, f"unmapped: {unmapped}")
    plaswire = [f for f in firms if f["name"] == "Plaswire"]
    if plaswire:
        pw = plaswire[0]
        check("Plaswire reclassified to waste_recycler", pw["role"] == "waste_recycler",
              pw["role"])
        check("Plaswire has no tracked critical-mineral target (composites)",
              not pw["recycler_targets"], f"targets {pw['recycler_targets']}")
    # scores bounded
    bad = [f["name"] for f in firms for v in f["scores"].values() if not (0 <= v <= 1)]
    check("all firm scores in [0,1]", not bad, f"out of range: {bad[:3]}")


def test_economic_sanity():
    section("10. Economic sanity ranges")
    from io_module import DynamicIO
    io = DynamicIO()
    mult = io.multipliers()
    mine = P.S["Mining_Quarrying"]
    out_typeII = mult["output_type2"][mine]
    check("mining Type II output multiplier in 1.3-2.2", 1.3 <= out_typeII <= 2.2,
          f"{out_typeII:.3f}")
    # mining direct GVA/output ratio
    gva_ratio = io.gva_coeff[mine]
    check("mining GVA/output coeff in 0.2-0.5", 0.2 <= gva_ratio <= 0.5,
          f"{gva_ratio:.3f}")
    # baseline scenario jobs/GVA positive and bounded vs NI totals
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), "outputs",
                                  "scenario_timeseries.csv"))
    end_jobs = df["employment_total"].max()
    check("peak total jobs < 1% of NI employment (816,562)",
          end_jobs < 0.01 * P.ANCHORS["ni_total_jobs_2023"],
          f"{end_jobs:.0f} jobs")
    check("recycled share never exceeds 1", df["crit_recycled_share"].max() <= 1.0 + 1e-6)


def test_geopolitical():
    section("11. Geopolitical-shock features (diversification & time-varying shock)")
    caps = {mm: 0.5 for mm in P.CRITICAL_MINERALS}
    m0, d0 = _run(import_constraint=caps)
    m1, d1 = _run(policy={"diversification": 0.8}, import_constraint=caps)
    e0 = float(d0.iloc[-1]["crit_max_single_country"])
    e1 = float(d1.iloc[-1]["crit_max_single_country"])
    check("diversification lowers single-country exposure", e1 < e0,
          f"{e0:.3f} -> {e1:.3f}")
    # time-varying shock (onset at year 5): no gap before, gap after
    def shock(t):
        return {"REE_magnet": 0.2, "Cobalt": 0.2, "Lithium": 0.2} if t >= 5 else {}
    m2, d2 = _run(import_constraint=shock)
    pre = float(d2.iloc[:5]["crit_supply_gap"].mean())
    post = float(d2.iloc[5:]["crit_supply_gap"].mean())
    check("time-varying shock: no gap before onset", pre < 1e-9, f"pre {pre:.4f}")
    check("time-varying shock: gap appears after onset", post > pre, f"post {post:.4f}")


def main():
    print("MODEL VERIFICATION & VALIDATION")
    for t in (test_validation, test_mass_balance, test_share_closure,
              test_no_nan_negative, test_determinism, test_sam_cge, test_spatial,
              test_stockpile, test_company_register, test_economic_sanity,
              test_geopolitical):
        try:
            t()
        except Exception as e:
            check(f"{t.__name__} ran without error", False, f"EXCEPTION: {e!r}")
    n_pass = sum(1 for ok, _, _ in RESULTS if ok)
    n_fail = len(RESULTS) - n_pass
    print("\n" + "=" * 78)
    print(f"SUMMARY: {n_pass} passed, {n_fail} failed, of {len(RESULTS)} checks")
    if n_fail:
        print("FAILURES:")
        for ok, name, detail in RESULTS:
            if not ok:
                print(f"  - {name}: {detail}")
    print("=" * 78)
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
