"""Stream objects passed between components.

Two kinds of streams appear in the SSME cycle:

* :class:`FluidStream` - a pure real fluid (para-H2, normal H2, O2) evaluated with the NIST tables;
* :class:`GasStream`   - an ideal-gas mixture (preburner/chamber gases) evaluated with NASA
  polynomials.  Its molar flows (mol/s) define both the composition and the mass flow.

Units everywhere: P [bar], T [K], m_dot [kg/s], h [kJ/kg], power/heat [kW].
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .thermo.fluids import RealFluid
from .thermo.hgs import Mixture


@dataclass(frozen=True)
class FluidStream:
    fluid: RealFluid
    m_dot: float
    P: float
    T: float

    @property
    def h(self) -> float:
        """Specific enthalpy on the table's own scale (use for differences within one fluid)."""
        return self.fluid.h(self.P, self.T)

    @property
    def s(self) -> float:
        return self.fluid.s(self.P, self.T)

    @property
    def rho(self) -> float:
        return self.fluid.rho(self.P, self.T)

    @property
    def h_abs(self) -> float:
        """Specific enthalpy on the NASA scale (use when mixing with gases / burning)."""
        return self.fluid.h_abs(self.P, self.T)

    @property
    def H_abs(self) -> float:
        """Enthalpy flow on the NASA scale, kW."""
        return self.m_dot * self.h_abs

    def as_mixture(self) -> Mixture:
        """Molar-flow representation of this stream as a single gas species."""
        return Mixture.from_mass_flows({self.fluid.species: self.m_dot})

    def with_(self, **kw) -> FluidStream:
        return replace(self, **kw)


@dataclass(frozen=True)
class GasStream:
    mix: Mixture  # molar flows, mol/s
    P: float
    T: float

    @property
    def m_dot(self) -> float:
        return self.mix.mass

    @property
    def h_abs(self) -> float:
        return self.mix.h_mass(self.T)

    @property
    def H_abs(self) -> float:
        return self.mix.H(self.T)

    @property
    def s(self) -> float:
        return self.mix.s_mass(self.T, self.P)

    @property
    def rho(self) -> float:
        """Ideal-gas density (no real-gas correction), kg/m^3."""
        return self.mix.density(self.T, self.P)

    def scaled_to(self, m_dot: float) -> GasStream:
        """Same composition and state, different mass flow (used for splitting a gas stream)."""
        f = m_dot / self.m_dot
        return GasStream(self.mix.with_n(self.mix.n * f), self.P, self.T)

    def with_(self, **kw) -> GasStream:
        return replace(self, **kw)


Stream = FluidStream | GasStream
