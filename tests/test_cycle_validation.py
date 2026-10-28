"""Validation of the cycle model against the SSME reference operating point.

Acceptance criteria live in ``src/ssme/data/ssme_reference.yaml`` (``acceptance``).  Every check
must pass except the *known deviations* listed below, each with its root cause.  The test fails if
a new deviation appears **or** if a known one disappears (then update this list and the docs).
"""

import pytest

from ssme.cycle import run_cycle

KNOWN_DEVIATIONS = {
    "isolated": {
        ("K26 HPFP", "W"): "reference W_ref is 3.3 % above m*dh of the reference states (data inconsistency)",
        ("K26 HPFP power vs states", "m*dh(reference states)"): "same data inconsistency, seen directly",
        ("HPFT", "W"): "HPFT W_ref is derived from K26 W_ref, so it inherits the 3.3 % inconsistency",
        ("K50 MCC", "T(S63)"): "reference chamber T exceeds the adiabatic equilibrium T from the reference inlets (open issue)",
    },
    "chained": {
        ("K26 HPFP", "W"): "reference W_ref inconsistent with reference states",
        ("K26 HPFP power vs states", "m*dh(reference states)"): "same data inconsistency",
        ("K50 MCC", "T(S63)"): "open issue (see isolated mode)",
        ("duct S51-S53", "T(S53)"): "+6.9 K OPB offset propagated (1.02 % vs 1 % criterion) plus 1.4 K duct loss not modelled",
    },
}


@pytest.mark.parametrize("mode", ["isolated", "chained"])
def test_only_known_deviations_fail(mode, isolated, chained):
    res = isolated if mode == "isolated" else chained
    failed = {(c.item, c.quantity) for c in res.failed}
    known = set(KNOWN_DEVIATIONS[mode])
    assert failed - known == set(), f"new validation failures: {sorted(failed - known)}"
    assert known - failed == set(), f"known deviations now pass, update the list: {sorted(known - failed)}"


def test_reference_mass_balances_close(isolated):
    for c in isolated.checks:
        if c.group == "balance" and c.item.startswith("mass"):
            assert c.passed, (c.item, c.computed, c.reference)


def test_para_hydrogen_reproduces_reference_and_normal_does_not(isolated, isolated_normal_h2):
    """The reference data were generated with para-hydrogen; the MATLAB code used normal H2."""
    para = isolated.check("K28 nozzle HX", "T(S36)")
    normal = isolated_normal_h2.check("K28 nozzle HX", "T(S36)")
    assert abs(para.error) < 1.0
    assert normal.error > 25.0
    assert len(isolated_normal_h2.failed) > len(isolated.failed)


def test_hp_oxidizer_turbine_as_gas_mixture(isolated):
    """HPOT K41 modelled as a frozen H2/H2O mixture reproduces the reference (pure H2 was ~80 % off in W)."""
    assert abs(isolated.check("K41 HPOT", "T(S51)").error) < 0.2
    assert abs(isolated.check("K41 HPOT", "W").rel_error) < 0.002


def test_lox_side_component_accuracy(isolated):
    for item, q in [("K10 LPOP", "T(S12)"), ("K12 mixer", "T(S13)"), ("K13 HPOP", "T(S14)"), ("K15 LPOT", "T(S160)"),
                    ("K18", "T(S21)"), ("K67 ox HX", "T(S80)"), ("K70 valve", "T(S69)")]:
        assert abs(isolated.check(item, q).error) < 0.15, item


def test_lox_recirculation_loop_converges(chained):
    assert chained.extras["lox_loop_iterations"]["n"] < 20


def test_nozzle_reference_inside_frozen_shifting_envelope(isolated, chained):
    for res in (isolated, chained):
        for q in ("T(S68)", "v(S68)", "M(S68)"):
            assert res.check("nozzle envelope", q).passed


def test_shaft_power_balances_in_reference_data(isolated):
    for c in isolated.checks:
        if c.item.startswith("shaft") and "reference data" in c.item:
            assert c.passed, c.item


def test_frozen_throat_nozzle_option_runs():
    res = run_cycle("isolated", nozzle_model="frozen_throat")
    assert res.check("nozzle envelope", "M(S68)").passed
