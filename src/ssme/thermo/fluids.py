"""Real fluids and a common enthalpy scale shared with the ideal-gas (NASA polynomial) mixtures.

Property backends
-----------------
``"nfp"``       NIST Webbook tables interpolated as in INIST/NFP (default; reproduces the MATLAB code)
``"coolprop"``  CoolProp Helmholtz equations of state (optional; used for cross-verification)

Both use the NIST default reference states (para/normal H2: h = s = 0 for saturated liquid at the
normal boiling point; O2: h = 271.013 kJ/kg at 298.15 K and 1 bar), so their absolute values are
directly comparable.

Why an enthalpy offset is needed
--------------------------------
The NASA polynomials use the absolute "formation" scale (h = 0 for the elements at 298.15 K).
Burners and gas mixers combine real-fluid inlets with gas mixtures, so every real-fluid enthalpy
must be moved onto the NASA scale first.

The original MATLAB ``getDeltah(P)`` matched the two curves *at the stream pressure* (e.g. 248 bar)
and 675 K, then applied that H2 offset to every species (H2O, OH, O2...).  At 248 bar hydrogen is
not an ideal gas, so the offset is wrong by ~200 kJ/kg, and an H2 offset is meaningless for other
species.  Here the offset of each fluid is computed in the ideal-gas limit, where the real-fluid
data and the NASA polynomials describe the same thing:

    offset = h_NASA(T_a) - h_real(p_a, T_a),     T_a = 300 K,  p_a = 0.01 bar

The NASA "H2" polynomial describes *normal* hydrogen, so para-H2 is tied to normal H2 through the
ortho->para conversion enthalpy of the saturated liquid at the normal boiling point
(``H2_NORMAL_TO_PARA_NBP``): both data sets are zeroed at their own NBP liquid, whose absolute
energies differ by exactly that amount.  ``tests/test_fluids.py`` checks this against the tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from . import coolprop_backend, hgs, nfp

ALIGN_T = 300.0  # K
ALIGN_P = 0.01  # bar
P_NBP = 1.01325  # bar
# Enthalpy released when saturated-liquid normal H2 (75 % ortho) converts to para-H2 at the NBP:
# 0.75 * E(J=1), E(J=1) = 2 k theta_rot with theta_rot = 85.3 K  ->  ~1063 J/mol  ->  ~527 kJ/kg.
H2_NORMAL_TO_PARA_NBP = 527.0  # kJ/kg

_HGS_NAME = {"H2": "H2", "pH2": "H2", "O2": "O2"}


class _NFPBackend:
    name = "nfp"
    h = staticmethod(nfp.h_pt)
    s = staticmethod(nfp.s_pt)
    rho = staticmethod(nfp.rho_pt)
    T_hp = staticmethod(nfp.t_hp)
    T_ps = staticmethod(nfp.t_ps)

    @staticmethod
    def h_sat_liquid(table: str, p: float) -> float:
        return nfp.NFP(table, "hl_p", p)


class _CoolPropBackend:
    name = "coolprop"
    h = staticmethod(coolprop_backend.h_pt)
    s = staticmethod(coolprop_backend.s_pt)
    rho = staticmethod(coolprop_backend.rho_pt)
    T_hp = staticmethod(coolprop_backend.t_hp)
    T_ps = staticmethod(coolprop_backend.t_ps)

    @staticmethod
    def h_sat_liquid(table: str, p: float) -> float:
        return coolprop_backend.props_si("H", "P", p * 1e5, "Q", 0.0, table) / 1e3


BACKENDS = {"nfp": _NFPBackend, "coolprop": _CoolPropBackend}


@dataclass(frozen=True)
class RealFluid:
    """A pure fluid ('H2' normal hydrogen, 'pH2' para-hydrogen, 'O2') with a property backend."""

    table: str
    backend: str = "nfp"

    def __post_init__(self):
        if self.table not in _HGS_NAME:
            raise ValueError(f"unknown fluid {self.table!r}; choose from {sorted(_HGS_NAME)}")
        if self.backend not in BACKENDS:
            raise ValueError(f"unknown backend {self.backend!r}; choose from {sorted(BACKENDS)}")
        if self.backend == "coolprop" and not coolprop_backend.available():
            raise RuntimeError("CoolProp backend requested but CoolProp is not available")

    @property
    def _b(self):
        return BACKENDS[self.backend]

    @property
    def species(self) -> str:
        """HGS species name used when this fluid enters a gas mixture."""
        return _HGS_NAME[self.table]

    @property
    def MM(self) -> float:
        """kg/mol"""
        return hgs.molar_mass(self.species) / 1000.0

    # native (NIST reference-state) scale -------------------------------------------------
    def h(self, p: float, T: float) -> float:
        return self._b.h(self.table, p, T)

    def s(self, p: float, T: float) -> float:
        return self._b.s(self.table, p, T)

    def rho(self, p: float, T: float) -> float:
        return self._b.rho(self.table, p, T)

    def T_hp(self, h: float, p: float) -> float:
        return self._b.T_hp(self.table, h, p)

    def T_ps(self, p: float, s: float) -> float:
        return self._b.T_ps(self.table, p, s)

    # absolute (NASA / HGS) scale ---------------------------------------------------------
    @property
    def offset(self) -> float:
        return enthalpy_offset(self.table, self.backend)

    def h_abs(self, p: float, T: float) -> float:
        """kJ/kg on the NASA-polynomial scale (formation enthalpy of H2 and O2 is zero)."""
        return self.h(p, T) + self.offset


@cache
def enthalpy_offset(table: str, backend: str = "nfp") -> float:
    """kJ/kg to add to a real-fluid enthalpy to put it on the NASA-polynomial scale."""
    b = BACKENDS[backend]
    if table == "pH2":
        normal_nbp = b.h_sat_liquid("H2", P_NBP)
        para_nbp = b.h_sat_liquid("pH2", P_NBP)
        return enthalpy_offset("H2", backend) + normal_nbp - para_nbp - H2_NORMAL_TO_PARA_NBP
    sp = hgs.species(_HGS_NAME[table])
    return sp.h(ALIGN_T) / sp.Mm * 1000.0 - b.h(table, ALIGN_P, ALIGN_T)


def getDeltah_original(P: float, table: str = "H2") -> float:
    """The original MATLAB ``getDeltah(P)`` (kept only to quantify its error): H2 at 675 K and P."""
    sp = hgs.species("H2")
    T = 675.0
    return sp.h(T) / sp.Mm * 1000.0 - nfp.h_pt(table, P, T)
