# Verification & Validation plan

This plan follows the usual split (e.g. AIAA G-077, ASME V&V 20):

- **Verification**: *are we solving the equations right?* This covers code verification (the implementation is
  correct) and solution verification (numerical error is small).
- **Validation**: *are we solving the right equations?* The model is compared with reference data, against
  acceptance criteria fixed beforehand.

Everything here is automated: `pytest` runs the whole matrix and `python -m ssme` writes the validation report.

## 1. Intended use and scope

A steady-state power balance of the SSME staged-combustion cycle at the reference operating point given in the
assignment. Two uses are covered:

| Mode | Question it answers |
|---|---|
| `isolated` (component validation) | Given the reference inlet state, does each component model reproduce the reference outlet? |
| `chained` (system validation) | Starting only from tank conditions, efficiencies, pressures, heat loads and flow splits, does the cycle reproduce the reference operating point? |

Out of scope for now: transients, off-design maps, pressure-drop prediction (pressures are imposed), and
combustion efficiency or finite-rate chemistry.

## 2. Reference data

`src/ssme/data/ssme_reference.yaml` holds the stations and components transcribed from the original scripts.
The tool that produced them is unknown. Its pedigree matters for validation: we can show *consistency* with
these data, not physical truth. The data-consistency checks found three issues, recorded under `data_issues`
in the YAML:

- copied densities at S90, S71 and S72;
- the HPFP power `W_ref`, which disagrees with the reference states by 3.3 %;
- two mass-flow typos.

## 3. Requirements and traceability

| ID | Requirement | Evidence (tests) |
|---|---|---|
| **V1** | NIST-table interpolation reproduces the tabulated values exactly at the nodes | `test_nfp.py::test_table_nodes_are_reproduced_exactly` |
| **V2** | Inverse functions T(h,p), T(p,s) are consistent with the forward ones; two-phase states are reported, not returned as T | `test_nfp.py::test_inverse_functions_round_trip`, `::test_two_phase_is_reported_not_silently_returned` |
| **V3** | Real-fluid properties agree with an independent implementation (CoolProp): ρ within 1 % over the SSME range; component outputs within 0.2 % (LPFT power: documented 3 % table error) | `test_coolprop_crosscheck.py` |
| **V4** | NASA polynomials reproduce JANAF at 298.15 K (h, s°, cp), are continuous at T_mid, and satisfy cp = dh/dT = T ds/dT | `test_hgs.py::test_species_against_janaf`, `::test_polynomials_continuous_at_tmid`, `::test_cp_is_derivative_of_h_and_t_ds` |
| **V5** | Equilibrium solver: element conservation to 1e-10, KKT stationarity, same minimum as a generic optimiser, correct limits | `test_hgs.py::test_equilibrium_*` |
| **V6** | Equilibrium + data agree with an independent code (RPA, LH2/LOX case): T within 2 K, composition within 2 % | `test_hgs.py::test_against_rpa_lh2_lox_case` |
| **V7** | Common enthalpy scale: NIST–NASA offsets constant in the ideal-gas limit; para-H2 offset consistent with the tables | `test_fluids.py` |
| **V8** | Components conserve mass, energy and elements; limiting cases hold (η = 1 is isentropic; pump + turbine at η = 1 is reversible; valve is isenthalpic; nozzle ordering frozen < frozen-throat < shifting) | `test_components.py` |
| **V9** | Results do not change unintentionally | `test_regression.py` (baseline `tests/data/golden.json`) |
| **V10** | The Python port agrees with the corrected MATLAB model (same data, same equations) | `test_matlab_crosscheck.py` (needs `export_results.m` to be run once in MATLAB) |
| **A1** | Component outlets match the reference within the acceptance criteria (§4) | `test_cycle_validation.py::test_only_known_deviations_fail[isolated]` |
| **A2** | Chained cycle matches the reference within the criteria; LOX loop converges | `test_cycle_validation.py::test_only_known_deviations_fail[chained]`, `::test_lox_recirculation_loop_converges` |
| **A3** | Mass balances close at every splitter/mixer; shaft power balances close (reference data and model) | `test_cycle_validation.py::test_reference_mass_balances_close`, `::test_shaft_power_balances_in_reference_data` |
| **A4** | Nozzle exit state of the reference lies inside the frozen/shifting-equilibrium envelope | `test_cycle_validation.py::test_nozzle_reference_inside_frozen_shifting_envelope` |

## 4. Acceptance criteria (proposed; please agree them with your supervisors)

Defined in the `acceptance` block of the YAML and applied automatically:

| Quantity | Criterion | Rationale |
|---|---|---|
| Cryogenic temperatures (< 200 K) | abs. error ≤ 2 K | ~1 % of the pump ΔT; comparable to the table interpolation error |
| Other temperatures | rel. error ≤ 1 % | ~10 K at preburner level |
| Pump/turbine power | rel. error ≤ 3 % | typical turbomachinery map uncertainty |
| Pressures from pressure ratios | rel. error ≤ 0.5 % | data given to 3 decimals |
| Densities | rel. error ≤ 0.5 % | NIST EOS uncertainty is ~0.1–0.2 % |
| Nozzle exit | reference inside [frozen, shifting] | the chemistry is between the two limits in reality |
| Mass balances | abs. error ≤ 0.02 kg/s | data given to 0.01 kg/s |

## 5. Current status

| Run | Pass | Fail | Report |
|---|---|---|---|
| isolated, para-H2, NIST tables | 88 | 4 | [docs/validation/isolated_pH2_nfp.md](validation/isolated_pH2_nfp.md) |
| chained, para-H2, NIST tables | 89 | 4 | [docs/validation/chained_pH2_nfp.md](validation/chained_pH2_nfp.md) |
| isolated, para-H2, CoolProp | 88 | 4 | [docs/validation/isolated_pH2_coolprop.md](validation/isolated_pH2_coolprop.md) |
| isolated, *normal* H2 (as the original) | 80 | 12 | [docs/validation/isolated_normalH2_nfp.md](validation/isolated_normalH2_nfp.md) |

Known deviations (each is asserted in `test_cycle_validation.py`, so a change in status is noticed):

1. **K26 HPFP power (−3.4 %)** and **HPFT power (+3.3 %)**: the reference `W_ref` disagrees with the reference
   states (data issue, FIX(17)).
2. **MCC temperature T(S63) (−1.4 %)**: the reference is above the adiabatic equilibrium temperature. This is an
   open issue (see the end of CODE_REVIEW.md).
3. *(chained only)* **duct S51→S53 (+1.02 %)**: the +6.9 K offset of the oxidizer preburner propagates. The duct heat
   loss (1.4 K in the reference) is not modelled.

## 6. Known model limitations (sources of model-form uncertainty)

- **Hot gas as an ideal gas.** The reference hot-gas densities agree with the ideal-gas density of the computed
  composition within 0.05 %, so the reference made the same assumption.
- **Frozen composition in the turbines and gas mixers** (justified below ~1100 K).
- **Isentropic nozzle**, with the regenerative heat removed from the kinetic energy at the exit, and no divergence or
  boundary-layer losses. That is why the nozzle is validated with an envelope.
- **Imposed pressures**: no pressure-drop or injector models, so pressures are validated only for consistency of the
  pressure ratios.
- **INIST tables**: 100-bar isobar spacing above 300 bar (FIX(18)). Use `--backend coolprop` when accuracy matters.
- **Para-H2 tied to the NASA (normal) H2 scale** through the 527 kJ/kg conversion enthalpy. The residual frozen
  ortho/para difference at 300–400 K is ≲ 10 kJ/kg (tested).

## 7. Suggested next steps

1. **Run the MATLAB cross-check once** (`legacy/matlab/fixed/export_results.m`) and commit
   `legacy/matlab/results/matlab_results.json`. This closes V10.
2. **Solution verification**: vary solver tolerances (brentq `xtol`, equilibrium `tol`) and show the outputs do not
   change. Add a convergence study of the HGS secant tolerances on the MATLAB side.
3. **Sensitivity analysis**: one-at-a-time ±1 % on efficiencies, heat loads and pressure ratios. Then a Monte Carlo
   run on the inputs to give validation errors an uncertainty band (`numpy.random`, ~1 s per cycle run).
4. **Resolve the open MCC issue** with whoever produced the reference data (species set, thermo database, heat-loss
   location).
5. **Close the cycle on pressure**: add duct/injector pressure-drop models, then solve for the turbine pressure ratios
   that balance the shafts. That would make the chained mode a real design-point solver.
6. Agree the acceptance criteria in §4 with your supervisors and record the agreement in this file.
