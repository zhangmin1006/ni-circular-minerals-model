# Q2.4 — What role should government have in ensuring secure mineral supply?

**Method (grounded in the strategy documents):** Vision 2035 warns that *"increasingly concentrated processing and mining supply chains"* leave supply *"vulnerable to shocks such as natural disasters, war or geopolitical fallout"*. We model that as a **dominant-supplier export ban** — per-mineral import caps = 1 − (2023 single-country concentration: REE 74% China, Co 70% DRC, Li 44% Australia; BGS/Idoine 2025) — escalated from trade friction to bloc fragmentation, plus a **Monte Carlo** of uncertain shocks (random onset, affected minerals ∝ concentration, severity). The five **government roles** are the postures the strategy itself describes — *optimise domestic production* and *build resilient UK & global supply networks* (incl. partnerships, diversification, stockpiling and circular capability). Metrics are the Vision-2035 / EU-CRMA secure-supply targets (≥10% domestic, ≥20% recycled, ≤60% single-country) plus an HHI-style supply-risk index and the unmet-demand supply gap. Figures are model behaviour, not forecasts.

## Roles tested

- **market_light_touch** — Market / light-touch
- **diversify_and_insure** — Diversify & insure (partnerships + stockpile)
- **domestic_autonomy** — Domestic autonomy (build primary)
- **circular_leader** — Circular leader (recover + recycle)
- **strategic_coordinator** — Strategic coordinator (balanced portfolio)

## Resilience under uncertainty (Monte Carlo, 120 random shocks)

| role | mean_supply_gap | p90_supply_gap | worst_supply_gap | mean_single_country_exposure | disc_public_cost_gbp_m |
|---|---|---|---|---|---|
| market_light_touch | 0.059 | 0.144 | 0.262 | 0.623 | 0.0 |
| diversify_and_insure | 0.056 | 0.135 | 0.252 | 0.4 | 121.8 |
| domestic_autonomy | 0.048 | 0.12 | 0.208 | 0.602 | 121.1 |
| circular_leader | 0.04 | 0.098 | 0.185 | 0.607 | 354.1 |
| strategic_coordinator | 0.034 | 0.079 | 0.159 | 0.427 | 515.9 |

- **Most resilient posture (lowest tail risk): `strategic_coordinator`** (Strategic coordinator (balanced portfolio)) — 90th-percentile supply gap 8% vs 14% under light-touch.

## Secure-supply metrics under an export-ban shock

| role | crit_domestic_share | crit_recycled_share | crit_import_share | single_country_exposure | supply_risk_index | mean_supply_gap | cum_disc_gva_gbp_m | disc_public_cost_gbp_m |
|---|---|---|---|---|---|---|---|---|
| market_light_touch | 0.011 | 0.135 | 0.65 | 0.246 | 0.223 | 0.129 | 771.5 | 0.0 |
| diversify_and_insure | 0.011 | 0.135 | 0.65 | 0.158 | 0.143 | 0.127 | 772.3 | 121.8 |
| domestic_autonomy | 0.076 | 0.135 | 0.634 | 0.246 | 0.218 | 0.105 | 989.6 | 121.1 |
| circular_leader | 0.011 | 0.204 | 0.65 | 0.246 | 0.223 | 0.069 | 1008.5 | 354.1 |
| strategic_coordinator | 0.076 | 0.199 | 0.61 | 0.18 | 0.154 | 0.063 | 1210.7 | 515.9 |

Vision-2035 targets: domestic ≥10%, recycled ≥20%, single-country ≤60%.

## Findings — the role government should play

1. **NI is structurally over-concentrated, and only diversification fixes it.** In normal times single-country exposure is ~85% under light-touch — far above the ≤60% target — and the *only* roles that meet the target are those that diversify imports (diversify-&-insure 54%, coordinator 61%). (Note: exposure *falls* under an actual export ban only because access to the dominant supplier is lost — that shows up instead as a **supply gap**, so the two must be read together.)
2. **Light-touch is not an option for security.** Under a dominant-supplier export ban the market posture leaves the widest supply gap and highest residual exposure — security is a public good the market under-provides.
3. **No single instrument is sufficient.** *Diversification + a stockpile* cut single-country exposure and bridge the immediate gap but build no domestic capability; *domestic autonomy* is slow and constrained by social licence and geology; *circular leadership* builds durable secondary supply but is feedstock-limited and cannot cover a broad shock alone.
4. **A balanced *strategic-coordinator* role is the most robust** across the shock range and the Monte-Carlo tail: it diversifies imports, holds a thin reserve to bridge, builds circular capacity for durable secondary supply, and brings responsible primary forward where social licence allows — the only posture that moves all three Vision-2035 indicators at once while adding GVA.
4b. **The coordinator role has institutional backing in the UK Industrial Strategy:** an enhanced **Critical Minerals Intelligence Centre** (horizon scanning = the *monitoring* function), **MoD/DSIT/DBT prioritisation of critical supply chains** (defence resilience + stockpiling), and an explicit aim to use **circular practices to boost resilient supply chains** — i.e. recycling capacity is itself a security instrument, linking Q2.4 to Q2.1/Q2.7.
5. **The government's role is therefore an active *coordinator/insurer*, not a producer or a bystander:** set the targets, de-risk midstream capacity (finance + offtake), fix feedstock collection, diversify and insure against the tail with partnerships + a strategic reserve, and uphold high-ESG/community-benefit terms. This is exactly what Vision 2035 describes — *"joint action between industry and government … in a more coordinated way"* across its dual objective of *optimising domestic production* and *building resilient UK & global supply networks*. The model finds that the posture the strategy actually adopts is also the most robust.

## Evidence on intervention effectiveness (real-world)

- **Japan is a validated natural experiment for exactly this policy mix.** After China's 2010 rare-earth export ban, Japan cut its dependence on Chinese REE from **~90% to ~58%** (now targeting <50%) through a *coordinated* programme: strategic stockpiling **+** overseas equity/offtake (JOGMEC brokered a **$250m Sojitz–Lynas** deal — equity & loans for guaranteed supply) **+** recycling **+** substitution. This is real-world confirmation that the **strategic-coordinator posture works**, and that diversification is achievable (~one-third+ cut over a decade — the basis for the model's diversification lever).
- **Stockpiles work as a bridge, not a fix (IEA).** Strategic stocks *"provide an important buffer against sudden disruptions while countries develop new diversified sources"* — the oil SPR is the decades-long precedent. This is exactly the model's finite, depleting reserve: it buys time while capacity and diversification are built.
- **The market moves the wrong way, so light-touch fails (IEA).** Diversification is *"the cornerstone of energy security, yet critical minerals are moving in the opposite direction"* — concentration is rising and near-term output growth stays with today's dominant producers. Security will not self-correct; active intervention is required.
- **Effective strategies coordinate across government (IEA/OECD).** The interventions that work align permitting, finance, industrial and environmental policy under a unified strategy — *"a departure from market-led approaches"* — and coordinate stockpile purchase/release internationally to avoid distorting the market. Again the **coordinator** role.

## Sources

- UK Critical Minerals Strategy — Vision 2035 (DBT): shock taxonomy (natural disasters, war, geopolitical fallout; concentrated processing & mining); two objectives; partnerships, diversification, defence stockpiling, responsible/high-ESG, coordinated industry–government action
- EU Critical Raw Materials Act (2024): 10% extraction / 40% processing / 25% recycling / ≤65% single-country benchmarks; strategic stockpiling & monitoring
- UK Industrial Strategy 2025: enhanced Critical Minerals Intelligence Centre (monitoring); MoD/DSIT/DBT critical-supply-chain prioritisation; circular practices to boost resilient supply chains
- BGS/Idoine et al. (2025) via GSNI OR25042: 2023 single-country supply concentration (REE 74%, Co 70%, Li 44%); ~80% of UK metals exported for processing
- Strategic stockpiles: Japan/JOGMEC 60–180 days, Korea/KOMIR 100 days (IEA; CSEP 2025)
- Japan post-2010 diversification: China REE dependence ~90%→~58%, targeting <50%; JOGMEC-brokered $250m Sojitz–Lynas equity/offtake deal (CNBC; WEF; New Security Beat 2024)
- IEA: stockpiles buffer disruptions 'while countries develop new diversified sources'; 'diversification is the cornerstone of energy security, yet critical minerals are moving in the opposite direction'; effective strategies coordinate across government (IEA Critical Minerals Policy Tracker / Security Programme 2025; OECD 2026)

*Roles are illustrative lever bundles; costs are NI-scale UK-anchored proxies for relative comparison. Behavioural thresholds and shock magnitudes are PROXY.*