"""
Compact recursive-dynamic CGE for Northern Ireland, calibrated to the NI SAM.

Single region, open economy:
  - Leontief intermediate demand (composite Armington goods)
  - Cobb-Douglas value added (capital, labour)
  - Armington CES (domestic vs imported) per commodity
  - Cobb-Douglas household demand; fixed real government & investment
  - Constant-elasticity export demand (falls in domestic price)
  - Factor markets clear: flexible wage & capital rental; fixed factor supplies
  - Numeraire: world price / exchange rate = 1

Verified by BENCHMARK REPLICATION (all excess demands ~0 at base prices).
Shocks (productivity, demand, factor supply) are applied and the new equilibrium
solved with scipy. A partial-equilibrium fallback (PEPriceLabour) is provided for
when a full solve is not warranted.

Elasticities are PROXY (sigma_arm=2.0, sigma_e=2.0). Value added is currently
Cobb-Douglas; replace with a true CES block if calibrated VA substitution data
are collected.
"""

import numpy as np
from scipy.optimize import root
import seed_parameters as P
from sam_module import build_sam

SIGMA_ARM = 2.0     # Armington domestic-import substitution
SIGMA_E = 2.0       # export demand elasticity


class CGE:
    def __init__(self, sam=None):
        self.sam = sam or build_sam()
        self.n = P.N
        self._calibrate()

    # ------------------------------------------------------------------ #
    def _calibrate(self):
        s = self.sam
        n = self.n
        self.X0 = s["output"].copy()
        self.VA0 = s["gva"].copy()
        self.L0 = s["labour"].copy()
        self.K0 = s["capital"].copy()
        self.va_coeff = self.VA0 / self.X0

        # total intermediate input coefficients on COMPOSITE goods
        dom_in = s["Z"].sum(axis=0)
        scale = np.where(dom_in > 0, (dom_in + s["imported_intermediates"]) / dom_in, 1.0)
        self.io = (s["Z"] * scale[None, :]) / self.X0[None, :]   # io[i,j]

        # base composite demand & Armington split
        C0 = s["household"]; G0 = s["gov"]; I0 = s["invest"]
        self.G0 = G0.copy(); self.I0 = I0.copy()
        QA0 = self.io @ self.X0 + C0 + G0 + I0
        self.D0 = np.maximum(self.X0 - s["exports"], 1e-6)       # domestic to home
        self.M0 = np.maximum(QA0 - self.D0, 1e-6)                # imports
        self.QA0 = self.D0 + self.M0
        self.C0 = C0.copy()
        self.EX0 = np.maximum(s["exports"], 1e-6)

        # --- Cobb-Douglas value added (sigma_va=1): replicates exactly as VA0=L0+K0 ---
        self.alphaL = self.L0 / (self.L0 + self.K0)              # labour cost share
        self.Bva = self.VA0 / (self.L0 ** self.alphaL * self.K0 ** (1 - self.alphaL))

        # --- Armington CES (Hosoe calibration, base PD0=PM0=1) ---
        rho_a = (SIGMA_ARM - 1) / SIGMA_ARM
        self.deltaA = (self.D0 ** (1 - rho_a)
                       / (self.D0 ** (1 - rho_a) + self.M0 ** (1 - rho_a)))
        self.Barm = self.QA0 / (self.deltaA * self.D0 ** rho_a
                                + (1 - self.deltaA) * self.M0 ** rho_a) ** (1 / rho_a)

        # --- household Cobb-Douglas budget shares ---
        Yh0 = self.L0.sum() + self.K0.sum()
        self.hh_spend = C0.sum()
        self.beta = C0 / self.hh_spend
        self.savings_rate = 1 - self.hh_spend / Yh0

        self.Lbar = self.L0.sum()
        self.Kbar = self.K0.sum()
        self.base = np.concatenate([np.ones(n), self.X0, [1.0, 1.0]])

    # ------------------------------------------------------------------ #
    def _unpack(self, v):
        n = self.n
        PD = v[:n]; X = v[n:2 * n]; w = v[2 * n]; r = v[2 * n + 1]
        return PD, X, w, r

    def _va_unit_cost(self, w, r, prod):
        # Cobb-Douglas unit cost; productivity 'prod' augments the scale Bva
        Beff = self.Bva * prod
        return (1 / Beff) * (w / self.alphaL) ** self.alphaL \
            * (r / (1 - self.alphaL)) ** (1 - self.alphaL)

    def _factor_demands(self, w, r, VA, prod):
        cva = self._va_unit_cost(w, r, prod)
        L = self.alphaL * cva * VA / w
        K = (1 - self.alphaL) * cva * VA / r
        return L, K

    def _armington(self, QA, PD, PM=1.0):
        # Hosoe-form Armington: composite price and domestic/import demand
        PA = (1 / self.Barm) * (self.deltaA ** SIGMA_ARM * PD ** (1 - SIGMA_ARM)
              + (1 - self.deltaA) ** SIGMA_ARM * PM ** (1 - SIGMA_ARM)
              ) ** (1 / (1 - SIGMA_ARM))
        D = QA / self.Barm * (self.Barm * self.deltaA * PA / PD) ** SIGMA_ARM
        M = QA / self.Barm * (self.Barm * (1 - self.deltaA) * PA / PM) ** SIGMA_ARM
        return D, M, PA

    def _residuals(self, v, shock):
        n = self.n
        PD, X, w, r = self._unpack(v)
        PD = np.maximum(PD, 1e-6); X = np.maximum(X, 1e-9)
        prod = shock.get("productivity", np.ones(n))     # VA productivity multiplier
        Lbar = self.Lbar * shock.get("labour_supply", 1.0)
        Kbar = self.Kbar * shock.get("capital_supply", 1.0)
        dem_shift = shock.get("demand_shift", np.ones(n))  # exo final-demand multiplier

        VA = self.va_coeff * X                          # real VA per output (fixed)
        cva = self._va_unit_cost(w, r, prod)

        # composite price index
        _, _, PA = self._armington(np.ones(n), PD)
        # price (zero-profit) residual: price = intermediate cost + VA cost
        res_price = PD - (self.io.T @ PA + cva * self.va_coeff)

        # demand side
        Yh = w * Lbar + r * Kbar
        C = self.beta * (1 - self.savings_rate) * Yh / PA
        G = self.G0 * dem_shift
        I = self.I0 * dem_shift
        QA = self.io @ X + C + G + I
        D, M, _ = self._armington(QA, PD)
        EX = self.EX0 * (PD / 1.0) ** (-SIGMA_E)
        res_output = X - (D + EX)

        L, K = self._factor_demands(w, r, VA, prod)
        res_L = L.sum() - Lbar
        res_K = K.sum() - Kbar
        return np.concatenate([res_price, res_output, [res_L, res_K]])

    # ------------------------------------------------------------------ #
    def solve(self, shock=None):
        shock = shock or {}
        sol = root(self._residuals, self.base, args=(shock,), method="hybr",
                   options={"xtol": 1e-10, "maxfev": 4000})
        PD, X, w, r = self._unpack(sol.x)
        VA = self.va_coeff * X
        return {
            "success": sol.success, "max_resid": np.abs(sol.fun).max(),
            "PD": PD, "X": X, "wage": w, "rental": r,
            "GVA": (VA * 1.0).sum(), "GVA_by_sector": VA,
            "wage_index": w, "real_GDP": X.sum(),
        }

    def benchmark_ok(self):
        r = self._residuals(self.base, {})
        return np.abs(r).max()


class PEPriceLabour:
    """Partial-equilibrium fallback: wage & price response to a sectoral demand
    shock via constant elasticities. Use when a full CGE solve is not warranted."""

    def __init__(self, sam=None, wage_elasticity=0.3, price_elasticity=0.2):
        self.sam = sam or build_sam()
        self.we = wage_elasticity
        self.pe = price_elasticity

    def response(self, extra_labour_demand_frac, extra_output_demand_frac):
        wage_change = self.we * extra_labour_demand_frac
        price_change = self.pe * extra_output_demand_frac
        return {"wage_change": wage_change, "price_change": price_change}


if __name__ == "__main__":
    cge = CGE()
    print("Benchmark replication max |excess demand|:", f"{cge.benchmark_ok():.2e}")
    base = cge.solve({})
    print("Base solve success:", base["success"], "max resid:", f"{base['max_resid']:.2e}")
    print("Base GVA (should be ~40000):", round(base["GVA"], 1))
    # shock: +20% productivity in mining + recycling
    prod = np.ones(P.N)
    prod[P.S["Mining_Quarrying"]] = 1.20
    prod[P.S["Recycling_Secondary"]] = 1.20
    sh = cge.solve({"productivity": prod})
    print("\nShock (+20% productivity mining+recycling):")
    print("  success:", sh["success"], " wage index:", round(sh["wage"], 4),
          " GVA:", round(sh["GVA"], 1),
          " dGVA%:", round(100 * (sh["GVA"] / base["GVA"] - 1), 3))
