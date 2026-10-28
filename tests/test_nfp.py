"""Verification of the real-fluid table layer (port of INIST/NFP)."""

import numpy as np
import pytest

from ssme.thermo import nfp
from ssme.thermo.nfp import NFPError, TwoPhaseError, load_table

FLUIDS = ["H2", "pH2", "O2"]


@pytest.mark.parametrize("fluid", FLUIDS)
def test_table_nodes_are_reproduced_exactly(fluid):
    """At a tabulated (P, T) node the interpolation must return the NIST value itself."""
    tab = load_table(fluid)
    rng = np.random.default_rng(0)
    for k in rng.integers(1, len(tab.isobars) - 1, size=15):
        iso = tab.isobars[k]
        for j in rng.integers(0, len(iso.T), size=5):
            if iso.split is not None and j in (iso.split, iso.split + 1):
                continue  # the phase-change node is double-valued by construction
            T = float(iso.T[j])
            if not (tab.tmin <= T <= tab.tmax):
                continue
            assert nfp.h_pt(fluid, iso.P, T) == pytest.approx(iso.props["h"][j], rel=1e-12, abs=1e-9)
            assert nfp.rho_pt(fluid, iso.P, T) == pytest.approx(iso.props["r"][j], rel=1e-12)


@pytest.mark.parametrize(
    "fluid,p,T",
    [("pH2", 2.07, 20.6), ("pH2", 486.49, 57.3), ("pH2", 431.4, 257.8), ("pH2", 345.5, 252.8),
     ("H2", 19.5, 22.7), ("O2", 6.89, 91.1), ("O2", 558.71, 116.8), ("O2", 285.53, 507.8), ("O2", 2.49, 494.0)],
)
def test_inverse_functions_round_trip(fluid, p, T):
    h = nfp.h_pt(fluid, p, T)
    s = nfp.s_pt(fluid, p, T)
    assert nfp.t_hp(fluid, h, p) == pytest.approx(T, abs=1e-7)
    assert nfp.t_ps(fluid, p, s) == pytest.approx(T, abs=1e-7)


def test_two_phase_is_reported_not_silently_returned():
    """MATLAB NFP returns [quality, Tsat] here, which the original code would treat as a temperature."""
    hl = nfp.NFP("O2", "hl_p", 5.0)
    hv = nfp.NFP("O2", "hv_p", 5.0)
    with pytest.raises(TwoPhaseError) as e:
        nfp.t_hp("O2", 0.5 * (hl + hv), 5.0)
    assert e.value.quality == pytest.approx(0.5, abs=1e-9)
    assert e.value.Tsat == pytest.approx(nfp.NFP("O2", "tsat_p", 5.0))


def test_out_of_range_raises():
    with pytest.raises(NFPError):
        nfp.h_pt("pH2", 800.0, 100.0)  # above the 700 bar isobar
    with pytest.raises(NFPError):
        nfp.h_pt("pH2", 10.0, 500.0)  # pH2 tables stop at 400 K


def test_monotonic_in_temperature_along_supercritical_isobar():
    T = np.linspace(40, 390, 200)
    h = [nfp.h_pt("pH2", 431.4, t) for t in T]
    assert np.all(np.diff(h) > 0)


def test_known_values_against_reference_densities():
    """Spot values: the assignment's densities match para-H2 better than normal H2."""
    assert nfp.rho_pt("pH2", 2.07, 20.6) == pytest.approx(70.57, rel=5e-4)
    assert abs(nfp.rho_pt("H2", 2.07, 20.6) - 70.57) > abs(nfp.rho_pt("pH2", 2.07, 20.6) - 70.57)
    assert nfp.rho_pt("O2", 6.89, 91.1) == pytest.approx(1137.99, rel=1e-4)


def test_isobar_spacing_above_300_bar_is_coarse():
    """Documented limitation: 100-bar spacing above 300 bar (SSME states sit at 330-560 bar)."""
    P = load_table("pH2").P
    assert list(P[-5:]) == [300.0, 400.0, 500.0, 600.0, 700.0]


@pytest.mark.parametrize("fluid", FLUIDS)
def test_data_files_carry_credit(fluid):
    """Each NIST table keeps its provenance (authors, repository, licence, original data) inside the file."""
    src = nfp.data_source(fluid)
    assert "Soria" in src["authors"] and "Fuster" in src["authors"] and "Frezza" in src["authors"]
    assert src["url"] == "https://github.com/ManelSoria/INIST" and src["license"] == "CC0-1.0"
    assert "NIST Chemistry WebBook" in src["data_origin"] and src["file"] == f"DatabaseNFP/{fluid}.mat"
