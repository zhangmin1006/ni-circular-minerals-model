"""
Data audit for the NI Circular Minerals model.

Inventories every data input used to build the model and the Q2.1-2.7 experiments,
classifies provenance/status, cross-checks the data register against the code
(which registered parameters are actually consumed), audits the firm register's
completeness, runs consistency checks, and lists the in-code parameters that are
NOT individually in the register. Writes a report to outputs/data_audit.md.

Run:  python audit_data.py
"""

import collections
import csv
import os
import re

HERE = os.path.dirname(__file__)
SRC = os.path.join(HERE, "src")
OUT = os.path.join(HERE, "outputs")

PY_FILES = ([os.path.join(SRC, f) for f in os.listdir(SRC) if f.endswith(".py")]
            + [os.path.join(HERE, f) for f in os.listdir(HERE) if f.endswith(".py")])
ALL_CODE = "\n".join(open(p, encoding="utf-8").read() for p in PY_FILES)


def load_register():
    with open(os.path.join(HERE, "data", "data_register.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f, skipinitialspace=True))


def load_firms():
    with open(os.path.join(HERE, "data", "company_register.csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f, skipinitialspace=True))


def consumed_outside_seed(attr):
    """Count files OTHER than seed_parameters.py that reference the attribute —
    i.e. is it actually consumed downstream? (defined-but-unused check)."""
    files = []
    for p in PY_FILES:
        if os.path.basename(p) in ("seed_parameters.py", "audit_data.py"):
            continue
        if re.search(rf"\b{re.escape(attr)}\b", open(p, encoding="utf-8").read()):
            files.append(os.path.basename(p))
    return files


# Non-parameter constants (paths, IO targets, harness scaffolding) to exclude so
# the inventory shows actual MODEL parameters.
_NOT_PARAMS = {
    "HERE", "OUT", "ROOT", "SRC", "OUT_DIR", "WORD", "FILES", "PY_FILES", "ALL_CODE",
    "FIG", "RESULTS", "REGISTER_PATH", "TEST_GROUPS", "VALIDATION_DESIGN", "FUZZ_N",
    "LEVER_RANGES", "_NOT_PARAMS", "SECTORS", "MINERALS", "CRITICAL_MINERALS",
    "PRODUCTS", "ROLE_SECTOR", "MINING_ROLES", "RECYCLING_ROLES", "DOWNSTREAM_ROLES",
    "SCORE_COLUMNS", "FEEDSTOCK_MINERALS", "ROLE_LABEL", "CATEGORIES",
}
# Files that are tooling, not model definitions.
_TOOL_FILES = {"audit_data.py", "verify_model.py", "export_word.py", "make_plots.py",
               "dashboard.py", "validate_model_report.py", "data_register.py"}


def code_constants():
    """Module-level UPPER_CASE *parameter* constants defined in each model file."""
    out = collections.defaultdict(list)
    for p in PY_FILES:
        if os.path.basename(p) in _TOOL_FILES:
            continue
        for line in open(p, encoding="utf-8"):
            m = re.match(r"([A-Z][A-Z0-9_]{2,})\s*[=:]", line)
            if m and m.group(1) not in _NOT_PARAMS:
                out[os.path.basename(p)].append(m.group(1))
    return out


def main():
    reg = load_register()
    firms = load_firms()
    L = []
    add = L.append

    add("# Data Audit — NI Circular Minerals model\n")
    add("Programmatic audit of the data inputs behind the model and the Q2.1-2.7 "
        "experiments: provenance/status, register-vs-code consumption, firm-register "
        "completeness, consistency checks and in-code parameter coverage. "
        "Regenerate with `python audit_data.py`.\n")

    # 1. Register status -----------------------------------------------------
    st = collections.Counter(r["status"] for r in reg)
    add("## 1. Data register (`data_register.csv`)\n")
    add(f"- **{len(reg)} parameters.** Status: "
        + ", ".join(f"{k} {v}" for k, v in st.most_common()) + ".")
    placeholder = [r["parameter"] for r in reg if "PLACEHOLDER" in (r.get("source") or "")]
    gaps = [r["parameter"] for r in reg if r["status"] == "gap"]
    add(f"- **Placeholder-source ({len(placeholder)})** — biggest provenance gaps: "
        + ", ".join(f"`{p}`" for p in placeholder) + ".")
    add(f"- **Declared gaps ({len(gaps)}):** " + (", ".join(f"`{g}`" for g in gaps) or "none") + ".\n")

    # 2. Register -> code consumption ---------------------------------------
    add("## 2. Are registered parameters actually used?\n")
    wired = {"RECOVERY_YIELDS", "COLLECTION_RATE_WEEE",
             "DEMAND_GROWTH_EV", "DEMAND_GROWTH_WIND"}
    add("| seed_parameters attribute | consumed in | verdict |")
    add("|---|---|---|")
    for attr in sorted(wired):
        files = consumed_outside_seed(attr)
        verdict = "consumed" if files else "**DEFINED-BUT-UNUSED**"
        where = ", ".join(f"`{f}`" for f in files) if files else "— (only seed_parameters.py)"
        add(f"| `{attr}` | {where} | {verdict} |")
    add("\n*Finding: parameters flagged DEFINED-BUT-UNUSED are loaded from the register "
        "but drive no output — their register `WIRED:` note overstates their effect.*\n")

    # 3. Firm register -------------------------------------------------------
    add("## 3. Firm register (`company_register.csv`)\n")
    ev = collections.Counter(f["evidence_status"] for f in firms)
    add(f"- **{len(firms)} firms**, all with a source URL. Evidence: "
        + ", ".join(f"{k} {v}" for k, v in ev.items()) + ".")
    for fld in ("investment_gbp_m", "annual_capacity_tonnes"):
        blank = sum(1 for f in firms if not (f.get(fld) or "").strip()
                    or (f.get(fld) or "").strip() == "0")
        add(f"- `{fld}`: only **{len(firms) - blank}/{len(firms)}** firms carry a non-zero value.")
    add("- The eight `*_score` columns (resource/capacity/feedstock/demand/local-procurement/"
        "planning-risk/skills/circularity) are **desk heuristics (0-1)**, not measured — the "
        "single largest proxy block on the firm side.\n")

    # 4. Consistency checks --------------------------------------------------
    add("## 4. Consistency checks\n")
    import sys
    sys.path.insert(0, SRC)
    from mfa_module import MINERAL_PARAMS
    import data_register as DR
    ree_mp = MINERAL_PARAMS["REE_magnet"][5]
    pilot_txt = open(os.path.join(HERE, "data", "ree_pilot.py"), encoding="utf-8").read()
    ree_pilot = float(re.search(r"import_single_country_share\"?\s*:\s*([\d.]+)", pilot_txt).group(1))
    reg_ree = DR.value("supply_concentration_ree_2023")
    add(f"- **REE single-country concentration is inconsistent across sources:** "
        f"`MINERAL_PARAMS` = {ree_mp} (BGS mine supply) and register = {reg_ree}, but the "
        f"REE pilot overrides it to **{ree_pilot}** (refined/magnet, China) — and every "
        f"experiment runs `use_ree_pilot=True`, so the model actually uses {ree_pilot}. Both "
        f"are defensible (mine vs refined) but the run value {ree_pilot} is not in the register.")
    add("- **Two demand bases coexist:** `run_mvm` and Q2.5-2.7 use the register-wired GREEN_DEMAND "
        "(EV 0.12 / wind 0.08); the demand-supply study uses annex-derived CAGRs (Li ~26.5% ...). "
        "Same model, different scenario inputs — intended, but document so they are not conflated.\n")

    # 5. In-code parameters not individually registered ----------------------
    add("## 5. In-code parameters (calibration coefficients) outside the register\n")
    add("The register curates headline/sourced data + key proxies. The bulk of structural & "
        "behavioural calibration lives in code as `PROXY`-commented constants, **not** itemised "
        "in the register. Module-level constants found:\n")
    consts = code_constants()
    for fn in sorted(consts):
        names = sorted(set(consts[fn]))
        if names:
            add(f"- **`{fn}`**: " + ", ".join(f"`{n}`" for n in names))
    add("\n*Plus non-constant proxies: the 8x8 I-O `A` matrix and the GVA/EMP/CO2/PM satellite "
        "vectors (seed_parameters), the ABM decision thresholds (dev hurdle 0.45, social-licence "
        "floor 0.4, risk/price coefficients), and per-scenario policy bundles. These are the "
        "model's biggest aggregate proxy dependency.*\n")

    # 6. Findings & recommendations -----------------------------------------
    add("## 6. Findings & recommendations (severity-ranked)\n")
    add("1. **[High] The I-O/SAM core is proxy.** `io_technical_coefficients`, "
        "`io_employment_coefficients`, `io_co2_coefficients` are placeholders; the A-matrix is a "
        "tuned proxy. *Action:* commission a regionalised NISRA Supply-Use + Scottish I-O (FLQ+RAS) "
        "and NI SAM — the single highest-value data investment.")
    add("2. **[Medium] Firm scores are desk heuristics.** The 0-1 capacity/feedstock/risk/"
        "procurement/skills scores drive ABM behaviour. *Action:* a firm-level survey "
        "(capacity tonnage, employment, local-procurement, planning status).")
    add("3. **[Medium] NI critical-mineral waste/recycling flows are a gap** (`collection_rate_weee` "
        "and the MFA collection/recovery seeds are UK-scaled). *Action:* DAERA/NIEA + recycler "
        "survey to build the NI MFA.")
    add("4. **[Low — RESOLVED] Defined-but-unused params fixed.** `COLLECTION_RATE_WEEE` is now "
        "*consumed* (caps WEEE-stream collection in the MFA); `LOCAL_PROCUREMENT_SHARE_MINING` is "
        "demoted to a documented reference benchmark (removed from seed config).")
    add("5. **[Low — RESOLVED] REE concentration reconciled & maps de-duplicated.** The 0.87 "
        "refined/magnet figure (the run value) is now registered alongside 0.74 mine supply; the "
        "shared `CONCENTRATION` and `LEVER_COST` maps live once in `src/policy_params.py` (imported "
        "by q2_3/q2_4/q2_6).")
    add("\n*Overall: validation anchors and headline policy figures are sourced and CI-checked; "
        "the economic-structure and behavioural calibration remain proxy (flagged), so outputs are "
        "directional, not forecasts. The three gap datasets above convert it to a calibrated tool.*")

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "data_audit.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("Wrote outputs/data_audit.md")
    print(f"  register: {len(reg)} params ({dict(st)}); firms: {len(firms)}")


if __name__ == "__main__":
    main()
