"""Real-fluid properties from tabulated NIST data: a Python port of INIST's ``NFP``.

The original MATLAB function (``NFP.m``, M. Soria, C. Fuster, L. Frezza, ESEIAAT-UPC, CC0,
https://github.com/ManelSoria/INIST)
interpolates NIST Webbook isobars:

1. linear interpolation in temperature along the two isobars that bracket ``p``
   (splitting each isobar at the liquid/vapour discontinuity), then
2. linear interpolation in pressure between those two isobars.

This module reproduces that algorithm exactly for the forward functions (``h_pt``, ``s_pt`` ...),
so results match the MATLAB toolchain to round-off.  The inverse functions (``t_hp``, ``t_ps``)
use a bracketed root finder instead of MATLAB's ``fsolve`` (which needs the Optimization Toolbox,
starts from an arbitrary guess and never checks its exit flag).  Where ``fsolve`` converged, both
give the same temperature to within the solver tolerance.

Units (same as INIST): T [K], p [bar], h [kJ/kg], s [kJ/(kg K)], rho [kg/m^3], cp/cv [kJ/(kg K)],
a [m/s], MM [kg/mol].

Note on the tables: above 300 bar the isobars are 100 bar apart (300, 400, 500, 600, 700 bar),
so linear interpolation in pressure carries a non-negligible error at the SSME's 330-560 bar
states.  ``tests/test_nfp.py`` quantifies it against CoolProp when CoolProp is available.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

DATA_DIR = Path(__file__).with_name("data")
AVAILABLE_FLUIDS = ("H2", "pH2", "O2")


class NFPError(ValueError):
    """Raised when a state is outside the tables or in an invalid region."""


class TwoPhaseError(NFPError):
    """Raised when an (h, p) or (s, p) pair falls inside the liquid-vapour dome."""

    def __init__(self, msg: str, quality: float, Tsat: float):
        super().__init__(msg)
        self.quality = quality
        self.Tsat = Tsat


@dataclass
class _Isobar:
    P: float
    T: np.ndarray
    props: dict[str, np.ndarray]
    split: int | None  # index q such that T[q] == T[q+1] (phase change), else None


@dataclass
class FluidTable:
    name: str
    isobars: list[_Isobar]
    P: np.ndarray
    Tcrit: float
    Pcrit: float
    MM: float
    reference_state: str
    sat: dict[str, np.ndarray] = field(repr=False)

    # ------------------------------------------------------------------ helpers
    @property
    def pmin(self) -> float:
        return float(self.P[0])

    @property
    def pmax(self) -> float:
        return float(self.P[-1])

    @property
    def tmin(self) -> float:
        # NFP's 'mint' uses the first isobar
        return float(self.isobars[0].T[0])

    @property
    def tmax(self) -> float:
        return float(self.isobars[0].T[-1])

    def _check_p(self, p: float) -> None:
        if not (self.pmin <= p <= self.pmax):
            raise NFPError(f"p={p:g} bar out of range of {self.name} tables ({self.pmin:g} to {self.pmax:g} bar)")

    def _check_T(self, T: float) -> None:
        if not (self.tmin <= T <= self.tmax):
            raise NFPError(f"T={T:g} K out of range of {self.name} tables ({self.tmin:g} to {self.tmax:g} K)")

    def _bracket(self, p: float) -> int:
        """Index i of the isobar pair (i, i+1) with P[i] <= p <= P[i+1] (first match, as NFP's findp)."""
        i = int(np.searchsorted(self.P, p, side="left")) - 1
        i = min(max(i, 0), len(self.P) - 2)
        return i

    @staticmethod
    def _myi(iso: _Isobar, prop: str, T: float) -> float:
        """NFP's ``myi``: 1-D interpolation that does not straddle the phase-change jump."""
        X = iso.T
        Y = iso.props[prop]
        if T < X[0]:
            raise NFPError(f"T={T:g} K below isobar p={iso.P:g} bar (starts at {X[0]:g} K)")
        if T > X[-1]:
            raise NFPError(f"T={T:g} K above isobar p={iso.P:g} bar (ends at {X[-1]:g} K)")
        q = iso.split
        if q is None:
            return float(np.interp(T, X, Y))
        if T <= X[q]:
            return float(np.interp(T, X[: q + 1], Y[: q + 1]))
        return float(np.interp(T, X[q + 1 :], Y[q + 1 :]))

    # ------------------------------------------------------------------ forward
    def prop_pt(self, prop: str, p: float, T: float) -> float:
        self._check_p(p)
        self._check_T(T)
        i = self._bracket(p)
        a, b = self.isobars[i], self.isobars[i + 1]
        v1 = self._myi(a, prop, T)
        v2 = self._myi(b, prop, T)
        return float(np.interp(p, [a.P, b.P], [v1, v2]))

    def sat_p(self, prop: str, p: float) -> float:
        if not (self.sat["Psat"][0] <= p <= self.sat["Psat"][-1]):
            raise NFPError(f"p={p:g} bar outside the saturation range of {self.name}")
        return float(np.interp(p, self.sat["Psat"], self.sat[prop]))

    # ------------------------------------------------------------------ inverse
    def _t_range(self, p: float) -> tuple[float, float]:
        i = self._bracket(p)
        a, b = self.isobars[i], self.isobars[i + 1]
        return max(a.T[0], b.T[0], self.tmin), min(a.T[-1], b.T[-1], self.tmax)

    def _invert(self, prop: str, value: float, p: float, sat_names: tuple[str, str]) -> float:
        self._check_p(p)
        if p < self.Pcrit:
            lo_name, hi_name = sat_names
            vl = self.sat_p(lo_name, p)
            vv = self.sat_p(hi_name, p)
            if vl <= value <= vv:
                Tsat = self.sat_p("Tsat", p)
                x = (value - vl) / (vv - vl)
                raise TwoPhaseError(
                    f"{self.name}: {prop}={value:g} at p={p:g} bar is inside the two-phase dome (x={x:.3f})", x, Tsat
                )
        Tlo, Thi = self._t_range(p)
        f = lambda T: self.prop_pt(prop, p, T) - value  # noqa: E731
        flo, fhi = f(Tlo), f(Thi)
        if flo * fhi > 0:
            raise NFPError(f"{self.name}: {prop}={value:g} at p={p:g} bar is outside the tabulated range")
        # The interpolated function is monotonic but has a jump at saturation for p < pcrit;
        # brentq still converges to the unique crossing.
        return float(brentq(f, Tlo, Thi, xtol=1e-10, rtol=1e-13, maxiter=200))


@cache
def load_table(fluid: str) -> FluidTable:
    if fluid not in AVAILABLE_FLUIDS:
        raise NFPError(f"Fluid {fluid!r} not available; choose one of {AVAILABLE_FLUIDS}")
    with np.load(DATA_DIR / f"nfp_{fluid}.npz") as npz:
        z = {k: npz[k] for k in npz.files}  # decompress each array once
    lengths = z["lengths"]
    starts = np.concatenate([[0], np.cumsum(lengths)[:-1]])
    isobars = []
    for k, (s, n) in enumerate(zip(starts, lengths)):
        T = z["iso_T"][s : s + n]
        props = {p: z[f"iso_{p}"][s : s + n] for p in ("h", "s", "r", "cp", "cv", "a")}
        dup = np.flatnonzero(np.diff(T) == 0)
        isobars.append(_Isobar(P=float(z["isobars"][k]), T=T, props=props, split=int(dup[0]) if dup.size else None))
    sat = {k: z[k] for k in ("Tsat", "Psat", "hl", "hv", "sl", "sv", "rl", "rv")}
    return FluidTable(
        name=fluid,
        isobars=isobars,
        P=z["isobars"],
        Tcrit=float(z["Tcrit"]),
        Pcrit=float(z["Pcrit"]),
        MM=float(z["MM"]),
        reference_state=str(z["reference_state"]),
        sat=sat,
    )


# ---------------------------------------------------------------------- public API (NFP-like)
_PT_PROPS = {"h_pt": "h", "s_pt": "s", "r_pt": "r", "cp_pt": "cp", "cv_pt": "cv", "a_pt": "a"}


def NFP(fluid: str, prop: str, *args: float) -> float:
    """Drop-in style access mirroring the MATLAB call signatures.

    ``NFP('H2', 'h_pt', p, T)``, ``NFP('H2', 't_hp', h, p)``, ``NFP('O2', 't_ps', p, s)``,
    ``NFP('O2', 'r_pt', p, T)``, ``NFP('H2', 'mm')``, ``NFP('H2', 'tsat_p', p)`` ...
    """
    tab = load_table(fluid)
    key = prop.lower()
    if key in _PT_PROPS:
        p, T = args
        return tab.prop_pt(_PT_PROPS[key], p, T)
    if key == "v_pt":
        p, T = args
        return 1.0 / tab.prop_pt("r", p, T)
    if key == "t_hp":
        h, p = args
        return tab._invert("h", h, p, ("hl", "hv"))
    if key == "t_ps":
        p, s = args
        return tab._invert("s", s, p, ("sl", "sv"))
    if key == "mm":
        return tab.MM
    if key == "tcrit":
        return tab.Tcrit
    if key == "pcrit":
        return tab.Pcrit
    if key == "tsat_p":
        return tab.sat_p("Tsat", args[0])
    if key == "psat_t":
        (T,) = args
        return float(np.interp(T, tab.sat["Tsat"], tab.sat["Psat"]))
    if key in ("hl_p", "hv_p", "sl_p", "sv_p", "rl_p", "rv_p"):
        return tab.sat_p(key[:2], args[0])
    if key == "minp":
        return tab.pmin
    if key == "maxp":
        return tab.pmax
    if key == "mint":
        return tab.tmin
    if key == "maxt":
        return tab.tmax
    raise NFPError(f"Unknown property {prop!r}")


def data_source(fluid: str) -> dict:
    """Provenance of a bundled table (authors, repository, commit, licence, origin of the data)."""
    with np.load(DATA_DIR / f"nfp_{fluid}.npz") as npz:
        return json.loads(str(npz["source"]))


def h_pt(fluid: str, p: float, T: float) -> float:
    return load_table(fluid).prop_pt("h", p, T)


def s_pt(fluid: str, p: float, T: float) -> float:
    return load_table(fluid).prop_pt("s", p, T)


def rho_pt(fluid: str, p: float, T: float) -> float:
    return load_table(fluid).prop_pt("r", p, T)


def cp_pt(fluid: str, p: float, T: float) -> float:
    return load_table(fluid).prop_pt("cp", p, T)


def t_hp(fluid: str, h: float, p: float) -> float:
    return load_table(fluid)._invert("h", h, p, ("hl", "hv"))


def t_ps(fluid: str, p: float, s: float) -> float:
    return load_table(fluid)._invert("s", s, p, ("sl", "sv"))
