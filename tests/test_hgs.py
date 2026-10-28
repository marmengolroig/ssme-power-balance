"""Verification of the ideal-gas thermochemistry layer (port of HGS)."""

import numpy as np
import pytest
from scipy.optimize import minimize

from ssme.thermo import hgs
from ssme.thermo.hgs import Mixture, R

H_O_SPECIES = ["H2", "O2", "H2O", "H", "O", "OH", "HO2", "H2O2"]


# ---------------------------------------------------------------- species data vs JANAF (298.15 K)
@pytest.mark.parametrize(
    "sp,dHf,S0,cp",
    [  # kJ/mol, J/(mol K), J/(mol K)  -- NIST-JANAF Thermochemical Tables, 4th ed.
        ("H2O", -241.826, 188.835, 33.590),
        ("H2", 0.0, 130.680, 28.836),
        ("O2", 0.0, 205.152, 29.376),
        ("H", 217.999, 114.716, 20.786),
        ("O", 249.173, 161.059, 21.911),
    ],
)
def test_species_against_janaf(sp, dHf, S0, cp):
    s = hgs.species(sp)
    assert s.h(298.15) == pytest.approx(dHf, abs=0.01)
    assert 1000 * s.s0(298.15) == pytest.approx(S0, abs=0.02)
    assert 1000 * s.cp(298.15) == pytest.approx(cp, abs=0.01)


@pytest.mark.parametrize("sp", H_O_SPECIES)
def test_polynomials_continuous_at_tmid(sp):
    s = hgs.species(sp)
    lo = hgs.Species(sp, s.Mm, s.Tmin, 1e9, s.Tmax, s.low, s.high, s.elements)
    hi = hgs.Species(sp, s.Mm, s.Tmin, 0.0, s.Tmax, s.low, s.high, s.elements)
    T = s.Tmid
    assert lo.h(T) == pytest.approx(hi.h(T), abs=1e-4)
    assert lo.cp(T) == pytest.approx(hi.cp(T), abs=1e-6)
    assert lo.s0(T) == pytest.approx(hi.s0(T), abs=1e-6)


@pytest.mark.parametrize("sp", ["H2O", "H2", "O2"])
def test_cp_is_derivative_of_h_and_t_ds(sp):
    s = hgs.species(sp)
    for T in (400.0, 1500.0, 3500.0):
        d = 1e-3
        assert (s.h(T + d) - s.h(T - d)) / (2 * d) == pytest.approx(s.cp(T), rel=1e-6)
        assert T * (s.s0(T + d) - s.s0(T - d)) / (2 * d) == pytest.approx(s.cp(T), rel=1e-6)


def test_mixture_properties_are_mole_weighted():
    m = Mixture(["H2", "H2O"], [2.0, 1.0])
    T = 900.0
    assert m.H(T) == pytest.approx(2 * hgs.species("H2").h(T) + hgs.species("H2O").h(T))
    assert m.Mm == pytest.approx((2 * 2.016 + 18.015) / 3)
    assert m.Cv(T) == pytest.approx(m.Cp(T) - 3 * R)
    # entropy of mixing: S = sum n_i s_i(T, x_i p)
    x = np.array([2, 1]) / 3
    S = sum(n * hgs.species(k).s(T, 5.0 * xi) for n, k, xi in zip([2, 1], ["H2", "H2O"], x))
    assert m.S(T, 5.0) == pytest.approx(S)


# ---------------------------------------------------------------- equilibrium
def _stoich(o_f_molar=0.5):
    return Mixture(H_O_SPECIES, [1.0, o_f_molar, 0, 0, 0, 0, 0, 0])


@pytest.mark.parametrize("T,p", [(1000.0, 400.0), (2500.0, 1.0), (3600.0, 220.0), (4500.0, 10.0)])
def test_equilibrium_conserves_elements_and_is_stationary(T, p):
    mix = _stoich(0.4)
    r = hgs.equilibrate_TP(mix, T, p)
    e0, e1 = mix.element_moles(), r.mixture.element_moles()
    for k in e0:
        assert e1[k] == pytest.approx(e0[k], rel=1e-10)
    # KKT stationarity: mu_j/RT = sum_i a_ij pi_i for every species present
    elems, A = r.mixture.element_matrix()
    n = r.mixture.n
    mu = np.array([s.g0(T) for s in r.mixture.sp]) / (R * T) + np.log(n / n.sum()) + np.log(p)
    resid = mu - A.T @ r.element_potentials
    major = n / n.sum() > 1e-12
    assert np.max(np.abs(resid[major])) < 1e-6


def test_equilibrium_matches_independent_gibbs_minimisation():
    """Cross-check the element-potential solver against a generic constrained optimiser."""
    T, p = 3200.0, 50.0
    mix = _stoich(0.5)
    r = hgs.equilibrate_TP(mix, T, p)
    elems, A = mix.element_matrix()
    b = A @ mix.n
    g = np.array([s.g0(T) for s in mix.sp]) / (R * T)

    def G(y):  # y = ln n
        n = np.exp(y)
        return float(np.dot(n, g + y - np.log(n.sum()) + np.log(p)))

    cons = {"type": "eq", "fun": lambda y: A @ np.exp(y) - b}
    y0 = np.log(np.full(len(mix.names), 0.3))
    sol = minimize(G, y0, constraints=[cons], method="SLSQP", options={"ftol": 1e-14, "maxiter": 1000})
    assert sol.success
    n_opt = np.exp(sol.x)
    x_opt, x_cea = n_opt / n_opt.sum(), r.mixture.n / r.mixture.n.sum()
    big = x_cea > 1e-3
    assert np.allclose(x_opt[big], x_cea[big], rtol=2e-4)
    assert G(np.log(r.mixture.n)) <= G(sol.x) + 1e-9  # ours is at least as low


def test_equilibrium_limits():
    # low temperature: complete combustion of a stoichiometric mixture
    r = hgs.equilibrate_TP(_stoich(0.5), 600.0, 10.0)
    assert r.mixture.mole_fractions()["H2O"] > 0.999999
    # very high temperature, low pressure: water mostly dissociated
    r = hgs.equilibrate_TP(_stoich(0.5), 4500.0, 0.1)
    assert r.mixture.mole_fractions()["H2O"] < 0.1


def test_against_rpa_lh2_lox_case():
    """Independent code-to-code validation against RPA (case of HGS example Ex13, RPA_H2_O2_ex.PNG).

    LH2/LOX, O/F = 4.1, 45 bar.  RPA's injector enthalpy (-988.1961 kJ/kg) is imposed so that the
    comparison isolates the equilibrium solver and the thermochemical data.  (Ex13 itself builds
    its inlet enthalpy from gaseous H2 at 90 K, -870 kJ/kg, so it cannot match RPA's H2(L).)
    """
    species = ["H2", "O2", "H2O", "OH", "O", "H", "HO2", "H2O2"]
    nH2 = 1.0 / (hgs.molar_mass("H2") / 1000)
    nO2 = 4.1 / (hgs.molar_mass("O2") / 1000)
    mix = Mixture(species, [nH2, nO2, 0, 0, 0, 0, 0, 0])
    r = hgs.equilibrate_HP(mix, -988.1961 * 5.1, 45.0)
    assert r.T == pytest.approx(3004.0779, abs=2.0)
    rpa = {"H": 0.0164185, "H2": 0.4730081, "H2O": 0.5040833, "O": 0.0001233, "O2": 0.0000519, "OH": 0.0063140}
    x = r.mixture.mole_fractions()
    for k, v in rpa.items():
        assert x[k] == pytest.approx(v, rel=0.02), k
    assert r.mixture.Mm == pytest.approx(10.1623, rel=1e-4)
    # shifting isentropic expansion: RPA throat 25.489 bar / 2764.71 K, exit 1 bar / 1534.13 K
    S0 = r.mixture.S(r.T, 45.0)
    assert hgs.equilibrate_SP(r.mixture, S0, 25.489).T == pytest.approx(2764.7096, abs=2.0)
    e = hgs.equilibrate_SP(r.mixture, S0, 1.0)
    assert e.T == pytest.approx(1534.1342, abs=2.0)
    assert e.mixture.Mm == pytest.approx(10.2809, rel=1e-4)


def test_hp_equilibrium_conserves_enthalpy():
    mix = _stoich(0.45)
    H0 = mix.H(800.0)
    r = hgs.equilibrate_HP(mix, H0, 30.0)
    assert r.mixture.H(r.T) == pytest.approx(H0, abs=1e-6 * abs(H0) + 1e-6)


def test_sp_equilibrium_conserves_entropy():
    mix = hgs.equilibrate_TP(_stoich(0.45), 3500.0, 200.0).mixture
    S0 = mix.S(3500.0, 200.0)
    r = hgs.equilibrate_SP(mix, S0, 1.0)
    assert r.mixture.S(r.T, 1.0) == pytest.approx(S0, rel=1e-9)


def test_temperature_outside_polynomial_range_raises():
    with pytest.raises(hgs.HGSError):
        hgs.species("H2").h(150.0)
