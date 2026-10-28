"""Ideal-gas mixture thermochemistry: a Python port of the parts of HGS used by the SSME model.

HGS (C. Fuster, M. Soria, A. Miró, ESEIAAT-UPC, CC0, https://github.com/ManelSoria/HGS) evaluates NASA 7-coefficient polynomials
(Burcat database) and finds chemical equilibrium by minimising the Gibbs energy with ``fmincon``.

Here:

* species properties use exactly the HGS formulas and coefficients (``HGSsingle``/``HGSprop``),
  including HGS's gas constant ``R = 8.3144621e-3 kJ/(mol K)``;
* equilibrium at fixed (T, p) uses the Gordon-McBride element-potential Newton method (as in
  NASA CEA) instead of a general-purpose optimiser.  For an ideal-gas mixture the Gibbs function
  is convex on the element-balance polytope, so both find the same unique minimum;
* (H, p) and (S, p) problems (adiabatic flame temperature, isentropic expansion) wrap the (T, p)
  solver in a bracketed root search, as HGS does with ``HGSsecant``.

Units follow HGS: T [K], p [bar], n [mol] (or mol/s), Mm [g/mol], h/g [kJ/mol], s/cp [kJ/(mol K)],
mixture H/G [kJ], S/Cp [kJ/K], sound speed [m/s].
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

R = 8.3144621e-3  # kJ/(mol K) -- value used by HGS (HGSr.m)
P_REF = 1.0  # bar
DATA_FILE = Path(__file__).with_name("data") / "nasa7_hgs.json"


class HGSError(ValueError):
    pass


@dataclass(frozen=True)
class Species:
    name: str
    Mm: float  # g/mol
    Tmin: float
    Tmid: float
    Tmax: float
    low: tuple[float, ...]
    high: tuple[float, ...]
    elements: Mapping[str, float]

    def coeffs(self, T: float) -> np.ndarray:
        if T < self.Tmin or T > self.Tmax:
            raise HGSError(f"T={T:.2f} K outside the NASA-polynomial range ({self.Tmin}-{self.Tmax} K) of {self.name}")
        return np.asarray(self.low if T <= self.Tmid else self.high)

    def cp(self, T: float) -> float:
        a = self.coeffs(T)
        return R * (a[0] + a[1] * T + a[2] * T**2 + a[3] * T**3 + a[4] * T**4)

    def h(self, T: float) -> float:
        a = self.coeffs(T)
        return R * (a[5] + a[0] * T + a[1] * T**2 / 2 + a[2] * T**3 / 3 + a[3] * T**4 / 4 + a[4] * T**5 / 5)

    def s0(self, T: float) -> float:
        """Standard-state (1 bar) entropy."""
        a = self.coeffs(T)
        return R * (a[6] + a[0] * np.log(T) + a[1] * T + a[2] * T**2 / 2 + a[3] * T**3 / 3 + a[4] * T**4 / 4)

    def s(self, T: float, p: float) -> float:
        """Entropy at partial pressure p (HGSs.m)."""
        return self.s0(T) - (R * np.log(p / P_REF) if p != 0 else 0.0)

    def g0(self, T: float) -> float:
        return self.h(T) - T * self.s0(T)


@lru_cache(maxsize=1)
def _database() -> dict[str, Species]:
    raw = json.loads(DATA_FILE.read_text())
    db = {}
    for name, d in raw.items():
        if name.startswith("_"):  # metadata ("_source": provenance and credit of the data)
            continue
        tmin, tmid, tmax = d["T_limits"]
        db[name] = Species(name, d["Mm"], tmin, tmid, tmax, tuple(d["low"]), tuple(d["high"]), d["elements"])
    return db


def species(name: str) -> Species:
    try:
        return _database()[name]
    except KeyError as exc:
        raise HGSError(f"Species {name!r} not in the bundled database ({sorted(_database())})") from exc


def data_source() -> dict:
    """Provenance of the bundled NASA-polynomial data (authors, repository, commit, licence, origin)."""
    return json.loads(DATA_FILE.read_text())["_source"]


def molar_mass(name: str) -> float:
    """g/mol (HGSsingle(name, 'Mm'))."""
    return species(name).Mm


# ---------------------------------------------------------------------------- mixtures
class Mixture:
    """An ideal-gas mixture given as species names and mole amounts (mol or mol/s)."""

    def __init__(self, names: Sequence[str], n: Iterable[float]):
        self.names = tuple(str(x) for x in names)
        self.n = np.asarray(list(n), dtype=float)
        if len(self.names) != self.n.size:
            raise HGSError("species and mole vectors have different lengths")
        if len(set(self.names)) != len(self.names):
            raise HGSError(f"duplicate species in {self.names}; merge them first (see Mixture.combine)")
        self.sp = [species(x) for x in self.names]

    # -- constructors -------------------------------------------------------------------
    @classmethod
    def from_dict(cls, comp: Mapping[str, float]) -> Mixture:
        return cls(list(comp.keys()), list(comp.values()))

    @classmethod
    def from_mass_flows(cls, flows: Mapping[str, float]) -> Mixture:
        """kg/s per species -> mol/s."""
        return cls(list(flows), [m * 1000.0 / molar_mass(k) for k, m in flows.items()])

    @staticmethod
    def combine(*mixtures: Mixture, extra_species: Sequence[str] = ()) -> Mixture:
        """Merge streams species-by-species (what the MATLAB code did with unique/accumarray)."""
        comp: dict[str, float] = {}
        for m in mixtures:
            for k, v in zip(m.names, m.n):
                comp[k] = comp.get(k, 0.0) + float(v)
        for k in extra_species:
            comp.setdefault(k, 0.0)
        return Mixture.from_dict(comp)

    def as_dict(self) -> dict[str, float]:
        return dict(zip(self.names, self.n.tolist()))

    def with_n(self, n: np.ndarray) -> Mixture:
        return Mixture(self.names, n)

    # -- bulk properties -----------------------------------------------------------------
    @property
    def n_total(self) -> float:
        return float(self.n.sum())

    @property
    def Mm(self) -> float:
        """Mean molar mass, g/mol."""
        return float(np.dot(self.n, [s.Mm for s in self.sp]) / self.n.sum())

    @property
    def mass(self) -> float:
        """kg (or kg/s if n is in mol/s)."""
        return float(np.dot(self.n, [s.Mm for s in self.sp]) / 1000.0)

    def mass_fractions(self) -> dict[str, float]:
        m = np.array([s.Mm for s in self.sp]) * self.n
        return dict(zip(self.names, (m / m.sum()).tolist()))

    def mole_fractions(self) -> dict[str, float]:
        return dict(zip(self.names, (self.n / self.n.sum()).tolist()))

    def H(self, T: float) -> float:
        """kJ (kJ/s if n in mol/s)."""
        return float(sum(ni * s.h(T) for ni, s in zip(self.n, self.sp)))

    def Cp(self, T: float) -> float:
        return float(sum(ni * s.cp(T) for ni, s in zip(self.n, self.sp)))

    def Cv(self, T: float) -> float:
        return self.Cp(T) - R * self.n_total

    def S(self, T: float, p: float) -> float:
        nt = self.n_total
        total = 0.0
        for ni, s in zip(self.n, self.sp):
            if ni > 0:
                total += ni * s.s(T, p * ni / nt)
        return float(total)

    def G(self, T: float, p: float) -> float:
        return self.H(T) - T * self.S(T, p)

    def h_mass(self, T: float) -> float:
        """kJ/kg."""
        return self.H(T) / self.mass

    def s_mass(self, T: float, p: float) -> float:
        return self.S(T, p) / self.mass

    def Rg(self) -> float:
        """kJ/(kg K)."""
        return R / self.Mm * 1000.0

    def gamma_frozen(self, T: float) -> float:
        return self.Cp(T) / self.Cv(T)

    def sound_speed_frozen(self, T: float) -> float:
        """m/s, frozen composition (what HGSprop(...,'a') returns)."""
        return float(np.sqrt(self.gamma_frozen(T) * self.Rg() * 1e3 * T))

    def density(self, T: float, p: float) -> float:
        """kg/m^3, ideal gas."""
        return p * 1e5 / (self.Rg() * 1e3 * T)

    # -- element bookkeeping ---------------------------------------------------------------
    def element_matrix(self) -> tuple[list[str], np.ndarray]:
        elems = sorted({e for s in self.sp for e in s.elements})
        A = np.array([[s.elements.get(e, 0.0) for s in self.sp] for e in elems])
        return elems, A

    def element_moles(self) -> dict[str, float]:
        elems, A = self.element_matrix()
        return dict(zip(elems, (A @ self.n).tolist()))


# ---------------------------------------------------------------------------- equilibrium
@dataclass
class EquilibriumResult:
    mixture: Mixture
    T: float
    p: float
    iterations: int
    element_potentials: np.ndarray  # pi_i = lambda_i / RT


def equilibrate_TP(mix: Mixture, T: float, p: float, *, tol: float = 1e-11, max_iter: int = 500) -> EquilibriumResult:
    """Minimise G at fixed (T, p) over the species of ``mix`` subject to element conservation.

    Gordon & McBride (NASA RP-1311, 1994), ideal gases only, reduced Newton system in the element
    potentials and the total-moles correction.  Species with zero initial amount are allowed.
    """
    elems, A = mix.element_matrix()
    b0 = A @ mix.n
    keep = b0 > 0
    if not np.all(keep):  # an element with zero inventory: drop it and all species containing it
        bad = [e for e, k in zip(elems, keep) if not k]
        raise HGSError(f"elements {bad} have zero inventory; remove the species that contain them")
    scale = mix.mass  # work per kg of mixture (mol/kg) for conditioning
    b0s = b0 / scale
    ns = len(mix.names)
    g_rt = np.array([s.g0(T) for s in mix.sp]) / (R * T)
    ln_p = np.log(p / P_REF)

    # CEA initial estimate: n = 0.1 mol, split equally (the result does not depend on it)
    ln_nj = np.log(np.full(ns, 0.1 / ns))
    ln_n = np.log(0.1)
    pi = np.zeros(len(elems))
    for it in range(1, max_iter + 1):  # noqa: B007 (it is reported after the loop)
        nj = np.exp(ln_nj)
        n = np.exp(ln_n)
        mu = g_rt + ln_nj - ln_n + ln_p  # mu_j / RT
        # reduced (l+1) system
        l = len(elems)
        M = np.zeros((l + 1, l + 1))
        rhs = np.zeros(l + 1)
        Anj = A * nj  # a_ij n_j
        M[:l, :l] = Anj @ A.T
        M[:l, l] = Anj.sum(axis=1)
        M[l, :l] = Anj.sum(axis=1)
        M[l, l] = nj.sum() - n
        rhs[:l] = b0s - A @ nj + Anj @ mu
        rhs[l] = n - nj.sum() + nj @ mu
        try:
            sol = np.linalg.solve(M, rhs)
        except np.linalg.LinAlgError as exc:
            raise HGSError("singular equilibrium matrix") from exc
        pi = sol[:l]
        dln_n = sol[l]
        dln_nj = -mu + A.T @ pi + dln_n
        # CEA damping (RP-1311 eqs. 3.1-3.3)
        big = nj / n > 1e-8  # non-trace species (CEA "size" threshold, ln(1e8) = 18.42)
        denom1 = max(5 * abs(dln_n), np.max(np.abs(dln_nj[big])) if big.any() else 0.0)
        lam1 = 2.0 / denom1 if denom1 > 2.0 else 1.0
        lam2 = 1.0
        small = (~big) & (dln_nj >= 0)
        if small.any():
            with np.errstate(divide="ignore", invalid="ignore"):
                cand = np.abs((-ln_nj[small] + ln_n - 9.2103404) / (dln_nj[small] - dln_n))
            cand = cand[np.isfinite(cand)]
            if cand.size:
                lam2 = float(np.min(cand))
        lam = min(1.0, lam1, lam2)
        ln_nj = ln_nj + lam * dln_nj
        ln_n = ln_n + lam * dln_n
        ln_nj = np.maximum(ln_nj, ln_n - 80.0)  # keep trace species representable (x >= 1e-35)
        # convergence test (RP-1311 sec. 3.6, with a tighter tolerance than CEA's 0.5e-5)
        nj = np.exp(ln_nj)
        n = np.exp(ln_n)
        conv_j = np.max(nj * np.abs(dln_nj)) / nj.sum() <= tol
        conv_n = n * abs(dln_n) / nj.sum() <= tol
        elem_ok = np.max(np.abs(b0s - A @ nj)) <= 1e3 * tol * np.max(b0s)
        if conv_j and conv_n and elem_ok:
            break
    else:
        raise HGSError(f"equilibrium did not converge in {max_iter} iterations (T={T}, p={p})")
    return EquilibriumResult(mix.with_n(nj * scale), T, p, it, pi)


def _bracket_root(f, lo: float, hi: float, what: str) -> float:
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        raise HGSError(f"{what}: no sign change between {lo} K and {hi} K (f={flo:.4g}, {fhi:.4g})")
    return float(brentq(f, lo, hi, xtol=1e-9, rtol=1e-12, maxiter=200))


def t_range(mix: Mixture) -> tuple[float, float]:
    return max(s.Tmin for s in mix.sp), min(s.Tmax for s in mix.sp)


def equilibrate_HP(mix: Mixture, H_target: float, p: float, *, T_bounds: tuple[float, float] | None = None) -> EquilibriumResult:
    """Adiabatic (H, p) equilibrium: find T so that H_eq(T, p) = H_target [kJ or kJ/s]."""
    lo, hi = T_bounds or t_range(mix)
    cache: dict[float, EquilibriumResult] = {}

    def f(T: float) -> float:
        r = equilibrate_TP(mix, T, p)
        cache[T] = r
        return r.mixture.H(T) - H_target

    T = _bracket_root(f, lo, hi, "equilibrate_HP")
    return cache.get(T) or equilibrate_TP(mix, T, p)


def equilibrate_SP(mix: Mixture, S_target: float, p: float, *, T_bounds: tuple[float, float] | None = None) -> EquilibriumResult:
    """Isentropic shifting equilibrium: find T so that S_eq(T, p) = S_target [kJ/K or kJ/(K s)]."""
    lo, hi = T_bounds or t_range(mix)

    def f(T: float) -> float:
        r = equilibrate_TP(mix, T, p)
        return r.mixture.S(T, p) - S_target

    T = _bracket_root(f, lo, hi, "equilibrate_SP")
    return equilibrate_TP(mix, T, p)


def frozen_T_from_H(mix: Mixture, H_target: float) -> float:
    lo, hi = t_range(mix)
    return _bracket_root(lambda T: mix.H(T) - H_target, lo, hi, "frozen_T_from_H")


def frozen_T_from_S(mix: Mixture, S_target: float, p: float) -> float:
    lo, hi = t_range(mix)
    return _bracket_root(lambda T: mix.S(T, p) - S_target, lo, hi, "frozen_T_from_S")
