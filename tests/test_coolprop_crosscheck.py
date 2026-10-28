"""Cross-verification of the NIST-table backend against CoolProp (independent implementation).

Skipped automatically when CoolProp is not installed (``pip install CoolProp`` or set
``COOLPROP_LIBRARY`` to a CoolProp shared library).
"""

import numpy as np
import pytest

from ssme.cycle import run_cycle
from ssme.thermo import coolprop_backend as cpb
from ssme.thermo import nfp

from .conftest import requires_coolprop

pytestmark = [requires_coolprop, pytest.mark.coolprop]


@pytest.fixture(scope="module")
def cp_isolated():
    return run_cycle("isolated", backend="coolprop")


@pytest.mark.parametrize("fluid,Trange", [("pH2", (40.0, 390.0)), ("O2", (70.0, 990.0))])
def test_density_agreement_over_ssme_pressure_range(fluid, Trange):
    rng = np.random.default_rng(42)
    worst = 0.0
    for _ in range(200):
        P, T = rng.uniform(20.0, 600.0), rng.uniform(*Trange)
        worst = max(worst, abs(nfp.rho_pt(fluid, P, T) / cpb.rho_pt(fluid, P, T) - 1))
    assert worst < 0.01  # table interpolation error, worst case near the pseudo-critical region


def test_component_results_agree_between_backends(isolated, cp_isolated):
    for a, b in zip(isolated.checks, cp_isolated.checks):
        assert (a.item, a.quantity) == (b.item, b.quantity)
        if a.group not in ("component", "system") or a.computed == 0:
            continue
        rel = abs(b.computed / a.computed - 1)
        if (a.item, a.quantity) == ("K34 LPFT", "W"):
            # 100-bar isobar spacing above 300 bar in the NIST tables -> ~3 % error on the small
            # isentropic drop of the LPFT; CoolProp matches the reference power to 0.1 %.
            assert 0.02 < rel < 0.04
            assert abs(b.rel_error) < 0.005
            continue
        assert rel < 2e-3, (a.item, a.quantity, a.computed, b.computed)
