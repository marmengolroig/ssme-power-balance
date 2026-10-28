# ssme-cycle

A steady-state power-balance model of the **Space Shuttle Main Engine** (staged-combustion LH2/LOX cycle), with a
**verification & validation** suite against the reference operating point of the 2025 SSME assignment.

It is a Python port of the original MATLAB scripts (kept in [`legacy/matlab`](legacy/matlab)), with the errors found
in review corrected ([docs/CODE_REVIEW.md](docs/CODE_REVIEW.md)). The two property libraries the MATLAB code used,
[INIST](https://github.com/ManelSoria/INIST) and [HGS](https://github.com/ManelSoria/HGS), are ported too, with the
same data. The package therefore needs only `numpy`, `scipy` and `pyyaml`.

```
$ python -m ssme --format summary
isolated / pH2 / nfp: 88 pass, 4 fail, 15 info
  FAIL K26 HPFP: W                                  <- reference data inconsistency (3.3 %)
  FAIL HPFT: W                                      <- inherits the same inconsistency
  FAIL K50 MCC: T(S63)                              <- open issue, see docs/CODE_REVIEW.md
  FAIL K26 HPFP power vs states: m*dh(reference states)
```

## Quick start

```bash
git clone <this repo> && cd ssme-cycle
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # add ,coolprop for the independent property cross-check
pytest                             # the whole V&V matrix (~3 s)
python -m ssme                     # validation report (Markdown) on stdout
python -m ssme --mode chained      # propagate states through the cycle
python -m ssme --backend coolprop  # CoolProp instead of the NIST tables
python -m ssme --hydrogen H2       # normal hydrogen, as the original code (12 failures)
```

From Python:

```python
from ssme import run_cycle
res = run_cycle("isolated")                     # or "chained"
print(res.check("K41 HPOT", "T(S51)").computed)  # 760.88 K (reference 760.9 K)
for c in res.failed:
    print(c.item, c.quantity, c.computed, c.reference, c.note)
```

## What was wrong in the MATLAB version (summary)

| # | Problem | Effect |
|---|---|---|
| 1 | Normal hydrogen (`'H2'`) instead of para-hydrogen (`'pH2'`) | nozzle-coolant outlet 31 K too hot |
| 2 | `P_out = P_in*(2-deltaP)`, but `deltaP` is a pressure ratio | 356 instead of 387 bar after K61+K20 |
| 3 | Typos `S21.m_dot = 50.16` and `S40.m_dot = 19.34` | OPB 20 K too hot, splitter "error" −0.8 % |
| 4 | `getDeltah` / multispecies mixers mix enthalpy reference states | mixers unusable (~200 kJ/kg offset error) |
| 5 | HPOT computed as pure H2 | turbine power 80 % too high |
| 6 | Burner temperatures imposed instead of computed | combustors not validated |
| 7 | `char(cellstr(...))` species passed to HGS | possible species/mole scrambling (verify) |
| 8 | Atomic H missing from the products | chamber T +76 K |
| 9 | Nozzle subtracts the MCC heat twice | exit velocity −21 m/s |

There are 18 items in total, with evidence and fixes, in [docs/CODE_REVIEW.md](docs/CODE_REVIEW.md).

## Repository layout

```
src/ssme/
  thermo/nfp.py            real-fluid NIST tables (port of INIST NFP)
  thermo/hgs.py            NASA polynomials + chemical equilibrium (port of HGS)
  thermo/fluids.py         common enthalpy scale, property backends (NIST tables / CoolProp)
  components.py            pump, turbine, valve, HX, mixers, splitter, burner, gas turbine, nozzle
  cycle.py                 the SSME cycle, isolated & chained modes, validation checks
  data/ssme_reference.yaml reference stations, components, acceptance criteria, data issues
  report.py, __main__.py   Markdown/CSV reports, command line
tests/                     verification & validation suite (pytest)
docs/                      CODE_REVIEW, VV_PLAN, MODEL, generated validation reports
legacy/matlab/original/    the MATLAB scripts as received
legacy/matlab/fixed/       corrected MATLAB version + export script for the cross-check
tools/                     data conversion, bug-impact study, regression-baseline update
```

## Verification & validation

See [docs/VV_PLAN.md](docs/VV_PLAN.md) for the requirements and traceability matrix. In short:

- **Verification**:
  - table nodes are reproduced exactly;
  - JANAF values are reproduced at 298 K;
  - the equilibrium solver is checked against KKT conditions, a generic optimiser and **RPA** (ΔT < 1 K);
  - the NIST tables are cross-checked against **CoolProp**;
  - every component conserves mass, energy and elements and has correct limiting cases;
  - a regression baseline catches unintended changes;
  - a code-to-code comparison with the corrected MATLAB is ready (run `export_results.m` once).
- **Validation**: 92 checks against the reference point under proposed acceptance criteria. Every component
  (pumps, valves, heat exchangers, mixers, both preburners, all turbines) matches. The nozzle exit lies inside the
  frozen/shifting envelope. The 4 remaining failures are explained, and `test_cycle_validation.py` asserts on them so
  a change in status is caught.

| Highlight | Model | Reference |
|---|---|---|
| HPOT K41 outlet T / power | 760.88 K / −21 776 kW | 760.9 K / −21 770 kW |
| Nozzle-coolant outlet T(S36) | 258.15 K | 257.8 K |
| Mixer K49 outlet T(S59) | 974.8 K | 975.0 K |
| LOX side (pumps, LPOT, HX, valve) | all within 0.1 K | |

## Continuous integration

`.github/workflows/ci.yml` runs ruff and the test suite on Python 3.10–3.13, plus a job with CoolProp installed
for the cross-check.

## Acknowledgements

The thermodynamic layer of this package is a Python port of two MATLAB libraries from ESEIAAT, Universitat Politècnica
de Catalunya, and uses their data:

- **[HGS](https://github.com/ManelSoria/HGS)** (chemical equilibrium and NASA polynomials), by Caleb Fuster, Manel Soria,
  Arnau Miró et al.;
- **[INIST / NFP](https://github.com/ManelSoria/INIST)** (real-fluid NIST tables), by Manel Soria, Caleb Fuster and
  Lorenzo Frezza.

Thanks to their authors for releasing them into the public domain. The underlying data come from the Burcat
thermochemical database and the NIST Chemistry WebBook; full references are in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Data sources and licences

- NIST fluid tables (via INIST) and Burcat NASA polynomials (via HGS): both projects are CC0. See
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); the commits used are in `src/ssme/thermo/data/SOURCES.json`, and
  every data file carries its own provenance (`ssme.thermo.hgs.data_source()`, `ssme.thermo.nfp.data_source(fluid)`).
- The SSME reference data come from the course assignment.
- **No licence has been chosen for this repository yet.** Add one (e.g. MIT) before making it public.
