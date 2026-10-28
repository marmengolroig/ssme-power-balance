# Third-party notices and references

This package re-implements in Python two MATLAB libraries written at ESEIAAT (Universitat Politècnica de Catalunya),
and ships data converted from them. Both are dedicated to the public domain (CC0), so attribution is not legally
required; it is given here, in the source files and inside every data file because their authors' work made this
project possible.

## HGS - chemical equation solver (MATLAB)
C. Fuster, M. Soria, A. Miró, et al. - ESEIAAT, Universitat Politècnica de Catalunya.
https://github.com/ManelSoria/HGS - **CC0 1.0 Universal** (public domain dedication).

- `src/ssme/thermo/hgs.py` re-implements the HGS property formulas (`HGSsingle`, `HGSprop`) in Python, with the same
  gas constant. The chemical-equilibrium solver uses the element-potential method of Gordon & McBride [3] instead
  of HGS's `fmincon` call; the (H, p) and (S, p) problems follow HGS's approach of wrapping the (T, p) solver in a
  root search (`HGSsecant`).
- `src/ssme/thermo/data/nasa7_hgs.json` contains the NASA 7-coefficient polynomials of 14 species extracted from
  `HGSdata.mat`. HGS took them from the Burcat database [1].

## INIST / NFP - Non-ideal Fluid Properties (MATLAB)
M. Soria, C. Fuster, L. Frezza - ESEIAAT, Universitat Politècnica de Catalunya.
https://github.com/ManelSoria/INIST - **CC0 1.0 Universal**.

- `src/ssme/thermo/nfp.py` re-implements `NFP.m` in Python (same interpolation algorithm; the inverse functions use a
  bracketed root finder instead of `fsolve`).
- `src/ssme/thermo/data/nfp_*.npz` contain the isobar tables of normal H2, para-H2 and O2, converted from INIST's
  `DatabaseNFP/*.mat` (only the T, h, s, ρ, cp, cv and a columns are kept). INIST downloaded them from the NIST
  Chemistry WebBook [2], which evaluates the reference equations of state of Leachman et al. [4] (normal and
  para-hydrogen) and Schmidt & Wagner [5] (oxygen).

## Provenance of the data files
The exact upstream commits are listed in `src/ssme/thermo/data/SOURCES.json`, and `tools/convert_thermo_data.py`
regenerates the files from clones of the two repositories. Each data file also carries its own credit: the
`"_source"` entry of `nasa7_hgs.json` and the `source` entry of each `.npz` (also available from Python as
`ssme.thermo.hgs.data_source()` and `ssme.thermo.nfp.data_source(fluid)`).

## CoolProp (optional)
I.H. Bell, J. Wronski, S. Quoilin, V. Lemort [6]. MIT licence. Used only for cross-verification when installed; not
distributed with this repository.

## References
1. A. Burcat and B. Ruscic, *Third Millennium Ideal Gas and Condensed Phase Thermochemical Database for Combustion
   with Updates from Active Thermochemical Tables*, ANL-05/20 and TAE 960, Argonne National Laboratory and Technion -
   Israel Institute of Technology, 2005.
2. E.W. Lemmon, I.H. Bell, M.L. Huber and M.O. McLinden, "Thermophysical Properties of Fluid Systems", in *NIST
   Chemistry WebBook, NIST Standard Reference Database Number 69*, eds. P.J. Linstrom and W.G. Mallard, National
   Institute of Standards and Technology, Gaithersburg MD, https://webbook.nist.gov/chemistry/fluid/.
3. S. Gordon and B.J. McBride, *Computer Program for Calculation of Complex Chemical Equilibrium Compositions and
   Applications. I. Analysis*, NASA Reference Publication 1311, 1994.
4. J.W. Leachman, R.T. Jacobsen, S.G. Penoncello and E.W. Lemmon, "Fundamental Equations of State for Parahydrogen,
   Normal Hydrogen, and Orthohydrogen", *J. Phys. Chem. Ref. Data* 38 (2009) 721-748.
5. R. Schmidt and W. Wagner, "A new form of the equation of state for pure substances and its application to
   oxygen", *Fluid Phase Equilibria* 19 (1985) 175-200.
6. I.H. Bell, J. Wronski, S. Quoilin and V. Lemort, "Pure and Pseudo-pure Fluid Thermophysical Property Evaluation
   and the Open-Source Thermophysical Property Library CoolProp", *Ind. Eng. Chem. Res.* 53 (2014) 2498-2508.

Used only as comparison values in the tests:

7. M.W. Chase Jr., *NIST-JANAF Thermochemical Tables*, 4th ed., J. Phys. Chem. Ref. Data, Monograph 9, 1998
   (`tests/test_hgs.py::test_species_against_janaf`).
8. A. Ponomarenko, *RPA: Tool for Rocket Propulsion Analysis* (`tests/test_hgs.py::test_against_rpa_lh2_lox_case`, the case of HGS example Ex13).
