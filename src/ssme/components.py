"""Steady-state component models of the SSME staged-combustion cycle.

Every function is pure: it takes inlet stream(s) and parameters and returns the outlet stream(s)
plus a small dict of derived quantities (power, heat, ...).  Sign convention for power: positive
when absorbed by the fluid (pumps), negative when delivered by the fluid (turbines).

Pressure losses are given either as an outlet pressure or as a *pressure ratio*
``PR = P_in / P_out`` (> 1).  The original MATLAB code applied the ratios as
``P_out = P_in * (2 - PR)``, which is only a first-order approximation of ``P_in / PR`` and
gives e.g. 457.0 instead of 472.7 bar for K61 (PR = 1.182).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Literal

from scipy.optimize import brentq

from .streams import FluidStream, GasStream, Stream
from .thermo import hgs
from .thermo.hgs import Mixture

# Gas-phase species considered in combustion products (H/O system).  The original code omitted
# atomic hydrogen, which is a major radical at chamber temperatures (~1-3 mol-% at 3600 K).
PRODUCT_SPECIES = ("H2", "O2", "H2O", "H", "O", "OH", "HO2", "H2O2")


def outlet_pressure(P_in: float, *, P_out: float | None = None, PR: float | None = None) -> float:
    if (P_out is None) == (PR is None):
        raise ValueError("give exactly one of P_out or PR")
    if PR is not None:
        if PR <= 0:
            raise ValueError("pressure ratio must be positive")
        return P_in / PR
    return float(P_out)


# ----------------------------------------------------------------------------- real fluids
def pump(inlet: FluidStream, P_out: float, eta: float) -> tuple[FluidStream, dict]:
    """Adiabatic pump with isentropic efficiency ``eta``."""
    if not 0 < eta <= 1:
        raise ValueError("eta must be in (0, 1]")
    f = inlet.fluid
    h1, s1 = inlet.h, inlet.s
    T2s = f.T_ps(P_out, s1)
    h2s = f.h(P_out, T2s)
    h2 = h1 + (h2s - h1) / eta
    T2 = f.T_hp(h2, P_out)
    out = inlet.with_(P=P_out, T=T2)
    return out, {"W": inlet.m_dot * (h2 - h1), "T_isentropic": T2s, "dh_isentropic": h2s - h1}


def turbine(inlet: FluidStream, P_out: float, eta: float) -> tuple[FluidStream, dict]:
    """Adiabatic real-fluid turbine (hydraulic LOX turbine or H2 turbine)."""
    if not 0 < eta <= 1:
        raise ValueError("eta must be in (0, 1]")
    f = inlet.fluid
    h1, s1 = inlet.h, inlet.s
    T2s = f.T_ps(P_out, s1)
    h2s = f.h(P_out, T2s)
    h2 = h1 + eta * (h2s - h1)
    T2 = f.T_hp(h2, P_out)
    out = inlet.with_(P=P_out, T=T2)
    return out, {"W": inlet.m_dot * (h2 - h1), "T_isentropic": T2s, "dh_isentropic": h2s - h1}


def valve(inlet: FluidStream, *, P_out: float | None = None, PR: float | None = None) -> tuple[FluidStream, dict]:
    """Isenthalpic throttling."""
    P2 = outlet_pressure(inlet.P, P_out=P_out, PR=PR)
    T2 = inlet.fluid.T_hp(inlet.h, P2)
    return inlet.with_(P=P2, T=T2), {}


def heat_exchanger(
    inlet: FluidStream, Q: float, *, P_out: float | None = None, PR: float | None = None
) -> tuple[FluidStream, dict]:
    """Heat ``Q`` [kW] added to the stream (negative to cool), with a pressure loss."""
    P2 = outlet_pressure(inlet.P, P_out=P_out, PR=PR)
    h2 = inlet.h + Q / inlet.m_dot
    T2 = inlet.fluid.T_hp(h2, P2)
    return inlet.with_(P=P2, T=T2), {"Q": Q, "dh": Q / inlet.m_dot}


def mixer(inlets: Sequence[FluidStream], P_out: float) -> tuple[FluidStream, dict]:
    """Adiabatic mixing of streams of the same real fluid."""
    fluid = inlets[0].fluid
    if any(s.fluid != fluid for s in inlets):
        raise ValueError("mixer() is for a single real fluid; use gas_mixer() for mixtures")
    m = sum(s.m_dot for s in inlets)
    H = sum(s.m_dot * s.h for s in inlets)
    T = fluid.T_hp(H / m, P_out)
    return FluidStream(fluid, m, P_out, T), {"dP_inlets": max(s.P for s in inlets) - min(s.P for s in inlets)}


def splitter(inlet: Stream, m_dot_1: float) -> tuple[Stream, Stream]:
    """Split a stream into two branches at the same state; branch 1 carries ``m_dot_1``."""
    if not 0 <= m_dot_1 <= inlet.m_dot * (1 + 1e-12):
        raise ValueError(f"branch flow {m_dot_1} outside [0, {inlet.m_dot}]")
    if isinstance(inlet, FluidStream):
        return inlet.with_(m_dot=m_dot_1), inlet.with_(m_dot=inlet.m_dot - m_dot_1)
    return inlet.scaled_to(m_dot_1), inlet.scaled_to(inlet.m_dot - m_dot_1)


# ----------------------------------------------------------------------------- gas side
def _as_mixture(s: Stream) -> Mixture:
    return s.as_mixture() if isinstance(s, FluidStream) else s.mix


def gas_mixer(inlets: Sequence[Stream], P_out: float, *, extra_species: Sequence[str] = ()) -> tuple[GasStream, dict]:
    """Adiabatic mixing into an ideal-gas mixture with frozen composition.

    Real-fluid inlets (e.g. cold H2) enter with their real enthalpy on the NASA scale, so the
    balance is consistent; the outlet is treated as an ideal-gas mixture.
    """
    mix = Mixture.combine(*[_as_mixture(s) for s in inlets], extra_species=extra_species)
    H = sum(s.H_abs for s in inlets)
    T = hgs.frozen_T_from_H(mix, H)
    return GasStream(mix, P_out, T), {"H_in": H}


def burner(
    inlets: Sequence[Stream],
    P_out: float,
    *,
    Q_loss: float = 0.0,
    species: Sequence[str] = PRODUCT_SPECIES,
) -> tuple[GasStream, dict]:
    """Adiabatic (or with heat loss ``Q_loss`` [kW]) chemical-equilibrium combustor at ``P_out``.

    Replaces the original approach of imposing the *reference* outlet temperature in ``HGSeq``,
    which made the combustor temperature an input instead of a prediction.
    """
    mix0 = Mixture.combine(*[_as_mixture(s) for s in inlets], extra_species=species)
    H_in = sum(s.H_abs for s in inlets)
    res = hgs.equilibrate_HP(mix0, H_in - Q_loss, P_out)
    return GasStream(res.mixture, P_out, res.T), {"H_in": H_in, "Q_loss": Q_loss, "iterations": res.iterations}


def equilibrium_state(inlets: Sequence[Stream], T: float, P: float, *, species: Sequence[str] = PRODUCT_SPECIES) -> GasStream:
    """Equilibrium composition of the combined inlets at an imposed (T, P) (the original approach)."""
    mix0 = Mixture.combine(*[_as_mixture(s) for s in inlets], extra_species=species)
    return GasStream(hgs.equilibrate_TP(mix0, T, P).mixture, P, T)


def gas_turbine(inlet: GasStream, P_out: float, eta: float) -> tuple[GasStream, dict]:
    """Adiabatic turbine for an ideal-gas mixture, frozen composition."""
    if not 0 < eta <= 1:
        raise ValueError("eta must be in (0, 1]")
    mix = inlet.mix
    S1 = mix.S(inlet.T, inlet.P)
    T2s = hgs.frozen_T_from_S(mix, S1, P_out)
    H1, H2s = mix.H(inlet.T), mix.H(T2s)
    H2 = H1 + eta * (H2s - H1)
    T2 = hgs.frozen_T_from_H(mix, H2)
    return GasStream(mix, P_out, T2), {"W": H2 - H1, "T_isentropic": T2s}


def gas_turbine_from_states(inlet: GasStream, outlet: GasStream) -> dict:
    """Power and implied isentropic efficiency of a gas turbine between two known states."""
    mix = inlet.mix
    S1 = mix.S(inlet.T, inlet.P)
    T2s = hgs.frozen_T_from_S(mix, S1, outlet.P)
    H1, H2, H2s = mix.H(inlet.T), mix.H(outlet.T), mix.H(T2s)
    return {"W": H2 - H1, "eta": (H2 - H1) / (H2s - H1), "T_isentropic": T2s}


def gas_turbine_for_power(inlet: GasStream, P_out: float, W: float) -> tuple[GasStream, dict]:
    """Turbine whose power is imposed (shaft power balance); returns outlet and required efficiency."""
    mix = inlet.mix
    H2 = mix.H(inlet.T) + W
    T2 = hgs.frozen_T_from_H(mix, H2)
    out = GasStream(mix, P_out, T2)
    return out, gas_turbine_from_states(inlet, out)


NozzleModel = Literal["shifting", "frozen", "frozen_throat"]


def _throat_shifting(mix0: Mixture, S0: float, H0: float, P0: float) -> tuple[float, hgs.EquilibriumResult]:
    """Throat of a shifting-equilibrium isentropic expansion (v = frozen sound speed, HGS convention)."""
    m = mix0.mass

    def f(P: float) -> float:
        r = hgs.equilibrate_SP(mix0, S0, P)
        dh = (H0 - r.mixture.H(r.T)) / m
        return math.sqrt(2000.0 * max(dh, 0.0)) - r.mixture.sound_speed_frozen(r.T)

    Pt = brentq(f, 0.3 * P0, 0.95 * P0, xtol=1e-8)
    return Pt, hgs.equilibrate_SP(mix0, S0, Pt)


def nozzle(
    chamber: GasStream,
    P_exit: float,
    *,
    Q_loss: float = 0.0,
    model: NozzleModel = "shifting",
) -> dict:
    """Isentropic expansion of the chamber gas to ``P_exit`` with an enthalpy loss ``Q_loss`` [kW].

    ``model``:
      * ``"shifting"``      - chemical equilibrium all the way (upper bound on recombination);
      * ``"frozen"``        - composition frozen at the chamber (lower bound);
      * ``"frozen_throat"`` - shifting equilibrium up to the throat, frozen afterwards.

    The heat removed by the regenerative nozzle coolant is subtracted from the kinetic energy at
    the exit, as in the original ``throat_nozzle.m``.  The Mach number uses the frozen sound
    speed, as HGS does.
    """
    mix0 = chamber.mix
    S0 = mix0.S(chamber.T, chamber.P)
    H0 = mix0.H(chamber.T)
    extra: dict = {}
    if model == "shifting":
        res = hgs.equilibrate_SP(mix0, S0, P_exit)
        mix_e, T_e = res.mixture, res.T
    elif model == "frozen":
        mix_e, T_e = mix0, hgs.frozen_T_from_S(mix0, S0, P_exit)
    elif model == "frozen_throat":
        Pt, rt = _throat_shifting(mix0, S0, H0, chamber.P)
        mix_e = rt.mixture
        T_e = hgs.frozen_T_from_S(mix_e, mix_e.S(rt.T, Pt), P_exit)
        extra = {"P_throat": Pt, "T_throat": rt.T}
    else:
        raise ValueError(f"unknown nozzle model {model!r}")
    H_e = mix_e.H(T_e)
    m = mix0.mass
    dh = (H0 - H_e - Q_loss) / m  # kJ/kg
    v = math.sqrt(2.0 * 1000.0 * dh) if dh > 0 else 0.0
    a = mix_e.sound_speed_frozen(T_e)
    return {
        "model": model,
        "T": T_e,
        "v": v,
        "a": a,
        "M": v / a,
        "rho": mix_e.density(T_e, P_exit),
        "Isp_momentum": v / 9.80665,  # s, momentum term only (no pressure thrust)
        "mixture": mix_e,
        "dh_isentropic": (H0 - H_e) / m,
        **extra,
    }
