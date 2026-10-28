# Third-party notices

## HGS - Hot Gas Simulator (MATLAB)
C. Fuster, M. Soria, A. Miró - ESEIAAT, Universitat Politècnica de Catalunya.
https://github.com/ManelSoria/HGS - **CC0 1.0 Universal** (public domain dedication).

`src/ssme/thermo/hgs.py` re-implements the HGS property formulas in Python.
`src/ssme/thermo/data/nasa7_hgs.json` contains NASA 7-coefficient polynomials for a subset of species, extracted from
`HGSdata.mat` (originally from the Burcat thermochemical database). The chemical-equilibrium solver uses the
element-potential method of Gordon & McBride, *NASA RP-1311* (1994), instead of HGS's `fmincon` call.

## INIST - Interpolation of NIST tables (MATLAB)
M. Soria, C. Fuster, L. Frezza - ESEIAAT, Universitat Politècnica de Catalunya.
https://github.com/ManelSoria/INIST - **CC0 1.0 Universal**.

`src/ssme/thermo/nfp.py` re-implements `NFP.m` in Python. `src/ssme/thermo/data/nfp_*.npz` contain the NIST Webbook
isobar tables of normal H2, para-H2 and O2, converted from INIST's `DatabaseNFP/*.mat` (only the T, h, s, ρ, cp, cv and a
columns are kept). The underlying data come from the NIST Chemistry WebBook (E.W. Lemmon, I.H. Bell, M.L. Huber,
M.O. McLinden, "Thermophysical Properties of Fluid Systems").

## CoolProp (optional)
I.H. Bell, J. Wronski, S. Quoilin, V. Lemort, *Ind. Eng. Chem. Res.* 53 (2014) 2498-2508. MIT licence. Used only
for cross-verification when installed; not distributed with this repository.

The exact upstream commits used to build the data files are listed in `src/ssme/thermo/data/SOURCES.json`, and
`tools/convert_thermo_data.py` regenerates them.
