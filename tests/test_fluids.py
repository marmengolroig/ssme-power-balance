"""Verification of the common enthalpy scale between real fluids and ideal-gas mixtures."""

import numpy as np
import pytest

from ssme.thermo import hgs, nfp
from ssme.thermo.fluids import H2_NORMAL_TO_PARA_NBP, RealFluid, enthalpy_offset, getDeltah_original


def _nasa_minus_nist(table: str, sp: str, T: float, p: float = 0.01) -> float:
    s = hgs.species(sp)
    return s.h(T) / s.Mm * 1000 - nfp.h_pt(table, p, T)


@pytest.mark.parametrize("table,sp,tol", [("H2", "H2", 12.0), ("O2", "O2", 0.2)])
def test_offset_is_constant_in_the_ideal_gas_limit(table, sp, tol):
    """NIST and NASA data must differ by a ~constant at low pressure (same substance, same physics).

    H2: 12 kJ/kg spread over 200-990 K is < 0.1 % of h, i.e. the NASA fit vs the NIST EOS.
    """
    T = np.linspace(200, 990, 12)
    d = [_nasa_minus_nist(table, sp, t) for t in T]
    assert max(d) - min(d) < tol
    assert enthalpy_offset(table) == pytest.approx(np.mean(d), abs=tol)


def test_para_offset_consistent_with_tables():
    """At 398 K frozen para-H2 and normal H2 nearly coincide; the NBP conversion enthalpy must explain the gap."""
    direct = _nasa_minus_nist("pH2", "H2", 398.0)
    assert enthalpy_offset("pH2") == pytest.approx(direct, abs=10.0)
    assert enthalpy_offset("pH2") == pytest.approx(enthalpy_offset("H2") - H2_NORMAL_TO_PARA_NBP, abs=0.01)


def test_original_getdeltah_error_is_large_at_cycle_pressures():
    """The MATLAB getDeltah(P) folded the real-gas departure at P into the offset (~200 kJ/kg at 248 bar)."""
    err = getDeltah_original(248.21) - enthalpy_offset("H2")
    assert err < -150.0
    assert abs(getDeltah_original(0.01) - enthalpy_offset("H2")) < 5.0


def test_absolute_enthalpy_of_ideal_gas_state_matches_nasa():
    f = RealFluid("O2")
    s = hgs.species("O2")
    assert f.h_abs(0.01, 700.0) == pytest.approx(s.h(700.0) / s.Mm * 1000, abs=0.2)


def test_unknown_fluid_or_backend_rejected():
    with pytest.raises(ValueError):
        RealFluid("N2")
    with pytest.raises(ValueError):
        RealFluid("O2", backend="refprop")
