# MATLAB versions

| Folder | Content |
|---|---|
| `original/` | The 13 files exactly as received (`20250113_SSME_Assignment.zip`). Kept for reference only. |
| `fixed/` | The corrected version. Every change is tagged `FIX(n)` with the number used in [docs/CODE_REVIEW.md](../../docs/CODE_REVIEW.md). |
| `results/` | Output of `fixed/export_results.m`, used by `tests/test_matlab_crosscheck.py`. |

## Running the corrected version

1. Clone the two libraries next to this repository (or set the `HGS_DIR` and `INIST_DIR` environment variables):
   ```
   git clone https://github.com/ManelSoria/HGS.git
   git clone https://github.com/ManelSoria/INIST.git
   ```
2. In MATLAB: `cd legacy/matlab/fixed`, then `main` (prints a comparison table) or `export_results`
   (also writes `../results/matlab_results.json`).
3. Commit `results/matlab_results.json`. `pytest` then compares every exported value with the Python port.

Requires the Optimization Toolbox (INIST's `fsolve`, HGS's `fmincon`).

> **The corrected MATLAB files were fixed by review but have not been executed** (no MATLAB was available).
> If something fails, the Python package is the tested reference.

## Changes with respect to `original/`

- `main.m`: rewritten as a clean component-validation script using the same station names.
  `mainLOX.m` was merged into it (and removed).
- `heatexanger.m`, `IsentalpicValve.m`: pressure ratio applied as `P_in/PR`.
- `pump.m`, `turbine.m`, `mixer.m`: two-phase guard; robust species input.
- New: `realfluid_offset.m` (replaces `getDeltah.m`), `realfluid_to_gas.m`, `burner_hp.m`, `mixer_gas.m`
  (replaces `mixer_multispecies*.m`), `turbine_mix.m`, `nozzle_exit.m` (replaces `throat_nozzle.m`),
  `check_single_phase.m`, `export_results.m`.
