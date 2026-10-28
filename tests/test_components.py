"""Verification of the component models: conservation laws, limiting cases, sign conventions."""

import pytest

from ssme import components as C
from ssme.streams import FluidStream, GasStream
from ssme.thermo import hgs
from ssme.thermo.fluids import RealFluid
from ssme.thermo.hgs import Mixture

PH2, O2 = RealFluid("pH2"), RealFluid("O2")


def lh2(m=10.0, P=19.5, T=22.7):
    return FluidStream(PH2, m, P, T)


def lox(m=50.0, P=29.7, T=92.3):
    return FluidStream(O2, m, P, T)


# ---------------------------------------------------------------------------- pressure ratio
def test_pressure_ratio_semantics():
    """PR = P_in / P_out (the original code used P_in*(2-PR), wrong for PR far from 1)."""
    assert C.outlet_pressure(463.32, PR=1.074) == pytest.approx(431.40, rel=1e-4)
    assert C.outlet_pressure(285.53, PR=285.53 / 2.49) == pytest.approx(2.49)
    with pytest.raises(ValueError):
        C.outlet_pressure(100.0)
    with pytest.raises(ValueError):
        C.outlet_pressure(100.0, P_out=50.0, PR=2.0)


# ---------------------------------------------------------------------------- pumps / turbines
@pytest.mark.parametrize("inlet,P_out", [(lh2(), 486.49), (lox(), 330.35)])
def test_pump_energy_balance_and_efficiency(inlet, P_out):
    out, d = C.pump(inlet, P_out, 0.7)
    assert d["W"] == pytest.approx(inlet.m_dot * (out.h - inlet.h), rel=1e-9)
    assert d["W"] > 0 and out.T > inlet.T and out.s > inlet.s
    # efficiency definition: dh_s / dh = eta
    assert d["dh_isentropic"] / (out.h - inlet.h) == pytest.approx(0.7, rel=1e-9)


@pytest.mark.parametrize("inlet,P_out", [(lh2(), 486.49), (lox(), 330.35)])
def test_isentropic_pump_then_turbine_returns_to_start(inlet, P_out):
    up, d1 = C.pump(inlet, P_out, 1.0)
    assert up.s == pytest.approx(inlet.s, abs=1e-6)
    back, d2 = C.turbine(up, inlet.P, 1.0)
    assert back.T == pytest.approx(inlet.T, abs=1e-5)
    assert d1["W"] + d2["W"] == pytest.approx(0.0, abs=1e-6 * d1["W"])


def test_turbine_sign_and_efficiency():
    inlet = FluidStream(PH2, 15.46, 345.5, 252.8)
    out, d = C.turbine(inlet, 261.36, 0.52)
    assert d["W"] < 0
    assert (out.h - inlet.h) / d["dh_isentropic"] == pytest.approx(0.52, rel=1e-9)


def test_efficiency_bounds():
    with pytest.raises(ValueError):
        C.pump(lh2(), 50.0, 0.0)
    with pytest.raises(ValueError):
        C.turbine(lh2(m=1, P=50, T=100), 20.0, 1.2)


# ---------------------------------------------------------------------------- valves, HX, mixers, splitters
def test_valve_is_isenthalpic():
    inlet = FluidStream(O2, 0.75, 285.53, 507.8)
    out, _ = C.valve(inlet, P_out=2.49)
    assert out.h == pytest.approx(inlet.h, abs=1e-6)
    assert out.T < inlet.T  # Joule-Thomson cooling of O2 at these conditions


def test_heat_exchanger_energy_balance():
    inlet = FluidStream(PH2, 28.88, 463.32, 59.1)
    out, d = C.heat_exchanger(inlet, 93130.0, PR=1.074)
    assert inlet.m_dot * (out.h - inlet.h) == pytest.approx(93130.0, rel=1e-9)
    assert out.P == pytest.approx(463.32 / 1.074)


def test_mixer_identical_streams_and_energy():
    a = lox(m=10.0, T=95.0)
    out, _ = C.mixer([a, a], a.P)
    assert out.T == pytest.approx(95.0, abs=1e-8) and out.m_dot == pytest.approx(20.0)
    b = lox(m=30.0, T=107.8)
    out, _ = C.mixer([a, b], 29.7)
    assert out.m_dot * out.h == pytest.approx(a.m_dot * a.h + b.m_dot * b.h, rel=1e-10)
    assert a.T < out.T < b.T


def test_mixer_rejects_different_fluids():
    with pytest.raises(ValueError):
        C.mixer([lox(), FluidStream(PH2, 1.0, 29.7, 100.0)], 29.7)


def test_splitter_conserves_mass_and_state():
    s1, s2 = C.splitter(lox(m=522.4, P=330.35, T=108.9), 83.06)
    assert s1.m_dot + s2.m_dot == pytest.approx(522.4)
    assert (s1.P, s1.T) == (s2.P, s2.T) == (330.35, 108.9)
    with pytest.raises(ValueError):
        C.splitter(lox(m=10.0), 11.0)


# ---------------------------------------------------------------------------- gas side
def _preburner():
    return C.burner([FluidStream(PH2, 19.94, 431.40, 163.3), FluidStream(O2, 13.56, 558.71, 116.8)], 387.25)


def test_burner_conserves_mass_elements_and_energy():
    h2, o2 = FluidStream(PH2, 19.94, 431.40, 163.3), FluidStream(O2, 13.56, 558.71, 116.8)
    gas, d = C.burner([h2, o2], 387.25)
    assert gas.m_dot == pytest.approx(19.94 + 13.56, rel=1e-10)
    e = gas.mix.element_moles()
    assert e["H"] == pytest.approx(2 * 19.94e3 / hgs.molar_mass("H2"), rel=1e-9)
    assert e["O"] == pytest.approx(2 * 13.56e3 / hgs.molar_mass("O2"), rel=1e-9)
    assert gas.H_abs == pytest.approx(h2.H_abs + o2.H_abs, rel=1e-8)


def test_burner_heat_loss_lowers_temperature():
    h2, o2 = FluidStream(PH2, 19.94, 431.40, 163.3), FluidStream(O2, 13.56, 558.71, 116.8)
    g0, _ = C.burner([h2, o2], 387.25)
    g1, _ = C.burner([h2, o2], 387.25, Q_loss=1000.0)
    assert g1.T < g0.T
    assert g0.H_abs - g1.H_abs == pytest.approx(1000.0, rel=1e-6)


def test_gas_mixer_energy_and_mass():
    gas, _ = _preburner()
    gas = gas.with_(P=248.21, T=759.5)
    h2 = FluidStream(PH2, 0.47, 248.21, 244.8)
    out, _ = C.gas_mixer([gas, h2], 248.21)
    assert out.m_dot == pytest.approx(gas.m_dot + 0.47, rel=1e-10)
    assert out.H_abs == pytest.approx(gas.H_abs + h2.H_abs, rel=1e-9)
    assert h2.T < out.T < gas.T


def test_gas_turbine_isentropic_limit_and_inverse():
    gas, _ = _preburner()
    out1, d1 = C.gas_turbine(gas, 251.43, 1.0)
    assert out1.mix.S(out1.T, out1.P) == pytest.approx(gas.mix.S(gas.T, gas.P), rel=1e-9)
    out, d = C.gas_turbine(gas, 251.43, 0.78)
    inv = C.gas_turbine_from_states(gas, out)
    assert inv["eta"] == pytest.approx(0.78, rel=1e-7)
    assert inv["W"] == pytest.approx(d["W"], rel=1e-9)
    out_p, dp = C.gas_turbine_for_power(gas, 251.43, d["W"])
    assert out_p.T == pytest.approx(out.T, abs=1e-6)


def _chamber():
    mix = Mixture.combine(Mixture.from_mass_flows({"H2": 1.0, "O2": 6.0}), extra_species=C.PRODUCT_SPECIES)
    return GasStream(hgs.equilibrate_TP(mix, 3600.0, 200.0).mixture, 200.0, 3600.0)


def test_nozzle_energy_conservation_and_model_ordering():
    ch = _chamber()
    res = {m: C.nozzle(ch, 0.2, model=m) for m in ("shifting", "frozen_throat", "frozen")}
    for r in res.values():
        assert 0.5 * r["v"] ** 2 / 1000 == pytest.approx(r["dh_isentropic"], rel=1e-9)
    # recombination releases heat: shifting is hottest and fastest, frozen coldest and slowest
    assert res["frozen"]["T"] < res["frozen_throat"]["T"] < res["shifting"]["T"]
    assert res["frozen"]["v"] < res["frozen_throat"]["v"] < res["shifting"]["v"]
    lossy = C.nozzle(ch, 0.2, Q_loss=1000.0, model="shifting")
    assert lossy["v"] < res["shifting"]["v"]
    assert lossy["T"] == pytest.approx(res["shifting"]["T"])  # loss applied to kinetic energy only


def test_nozzle_throat_is_sonic():
    ch = _chamber()
    r = C.nozzle(ch, 0.2, model="frozen_throat")
    assert 0.5 * ch.P < r["P_throat"] < 0.6 * ch.P  # ~0.55-0.58 Pc for gamma ~ 1.15-1.2
