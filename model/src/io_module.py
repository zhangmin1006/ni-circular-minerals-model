"""
Dynamic Input-Output module for the NI Circular Minerals MVM.

Implements:
  - Leontief inverse  L = (I - A)^-1
  - Type I multipliers (direct + indirect)
  - Type II multipliers (direct + indirect + induced) via a closed household row/col
  - Satellite accounts: GVA, employment, CO2, PM
  - DYNAMIC coefficients: A and import shares evolve each year under signals from
    the ABM (recycling substitution, local-procurement / leakage changes).

The matrix here is PROXY (see seed_parameters.py). The maths is the production
maths you will keep when the real regionalised NI table is dropped in.
"""

import numpy as np
import seed_parameters as P


class DynamicIO:
    def __init__(self):
        self.A0 = P.A.copy()          # base technical coefficients
        self.A = P.A.copy()           # current-year (may be modified dynamically)
        self.gva_coeff = P.GVA_COEFF.copy()
        self.emp_coeff = P.EMP_COEFF.copy()
        self.co2_coeff = P.CO2_COEFF.copy()
        self.pm_coeff = P.PM_COEFF.copy()
        self.import_share = P.IMPORT_SHARE.copy()
        self.N = P.N

    # ---- core Leontief --------------------------------------------------
    def leontief(self, A=None):
        A = self.A if A is None else A
        return np.linalg.inv(np.eye(self.N) - A)

    def closed_A(self):
        """Augment A with a household row (consumption) and column (income)
        to capture induced effects -> Type II."""
        n = self.N
        Ac = np.zeros((n + 1, n + 1))
        Ac[:n, :n] = self.A
        # household income column: wage share of GVA per unit output
        Ac[n, :n] = self.gva_coeff * P.WAGE_SHARE_OF_GVA
        # household consumption row: how wage income is spent across sectors,
        # scaled by local marginal propensity to consume (savings/tax/import leak out)
        Ac[:n, n] = P.HH_CONSUMPTION * P.LOCAL_CONSUMPTION_PROPENSITY
        return Ac

    # ---- impact of a final-demand vector --------------------------------
    def impact(self, final_demand, induced=True):
        """final_demand: length-N vector (£m). Returns dict of total impacts."""
        fd = np.asarray(final_demand, dtype=float)
        if induced:
            Ac = self.closed_A()
            Lc = np.linalg.inv(np.eye(self.N + 1) - Ac)
            fd_ext = np.append(fd, 0.0)
            x_ext = Lc @ fd_ext
            output = x_ext[:self.N]
        else:
            L = self.leontief()
            output = L @ fd

        gva = output * self.gva_coeff
        emp = output * self.emp_coeff
        co2 = output * self.co2_coeff
        pm = output * self.pm_coeff
        return {
            "output_by_sector": output,
            "output_total": output.sum(),
            "gva_total": gva.sum(),
            "employment_total": emp.sum(),
            "co2_total": co2.sum(),
            "pm_total": pm.sum(),
            "gva_by_sector": gva,
            "employment_by_sector": emp,
        }

    # ---- multipliers ----------------------------------------------------
    def multipliers(self):
        L1 = self.leontief()                       # Type I
        Ac = self.closed_A()
        L2 = np.linalg.inv(np.eye(self.N + 1) - Ac)[:self.N, :self.N]  # Type II
        return {
            "output_type1": L1.sum(axis=0),
            "output_type2": L2.sum(axis=0),
            "employment_type1": (L1 * self.emp_coeff[:, None]).sum(axis=0),
            "employment_type2": (L2 * self.emp_coeff[:, None]).sum(axis=0),
            "gva_type1": (L1 * self.gva_coeff[:, None]).sum(axis=0),
        }

    # ---- DYNAMIC coefficient update (driven by ABM) ---------------------
    def update_coefficients(self, recycling_substitution=0.0,
                            local_procurement_gain=0.0,
                            productivity_gain=0.0):
        """
        recycling_substitution : fraction of Manufacturing's mining input
                                 displaced by recycled/secondary material this year.
        local_procurement_gain : fractional reduction in mining import leakage
                                 (more inputs sourced in NI -> higher multipliers).
        productivity_gain       : fractional fall in all technical coefficients.
        """
        man = P.S["Manufacturing"]
        mine = P.S["Mining_Quarrying"]
        rec = P.S["Recycling_Secondary"]

        # Shift Manufacturing's demand from Mining -> Recycling (circular substitution)
        shift = self.A[mine, man] * recycling_substitution
        self.A[mine, man] -= shift
        self.A[rec, man] += shift

        # Local procurement: reduce mining import share -> retain more locally
        self.import_share[mine] *= (1.0 - local_procurement_gain)

        # Productivity: all coefficients shrink slightly
        if productivity_gain:
            self.A *= (1.0 - productivity_gain)

        np.clip(self.A, 0.0, 0.95, out=self.A)


if __name__ == "__main__":
    io = DynamicIO()
    m = io.multipliers()
    for i, s in enumerate(P.SECTORS):
        print(f"{s:22s} outI={m['output_type1'][i]:.2f} "
              f"outII={m['output_type2'][i]:.2f} "
              f"empII={m['employment_type2'][i]:.2f} jobs/£m")
