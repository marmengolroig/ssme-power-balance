"""Optional, independent real-fluid backend based on CoolProp (Helmholtz equations of state).

Used only for cross-verification of the tabulated NIST data (``nfp``): CoolProp implements the
same reference equations of state (Leachman et al. 2009 for normal/para hydrogen, Schmidt &
Wagner 1985 for oxygen) analytically, so differences between the two quantify the interpolation
error of the INIST tables.

Resolution order:

1. the ``CoolProp`` Python package (``pip install CoolProp``), or
2. a CoolProp shared library given by the ``COOLPROP_LIBRARY`` environment variable (ctypes).

If neither is available, :func:`available` returns ``False`` and the dependent tests are skipped.

Enthalpy/entropy reference states differ between CoolProp and the NIST tables, so only
*differences* (or quantities that do not depend on the reference: T, rho, cp, a) should be
compared directly.
"""

from __future__ import annotations

import ctypes
import os
from functools import lru_cache

# NFP table name -> CoolProp fluid name
FLUID_NAMES = {"H2": "Hydrogen", "pH2": "ParaHydrogen", "O2": "Oxygen"}


@lru_cache(maxsize=1)
def _impl():
    try:
        import CoolProp.CoolProp as CP  # type: ignore

        return ("python", CP.PropsSI)
    except Exception:
        pass
    lib_path = os.environ.get("COOLPROP_LIBRARY")
    if lib_path and os.path.exists(lib_path):
        lib = ctypes.CDLL(lib_path)
        f = lib.PropsSI
        f.restype = ctypes.c_double
        f.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_double, ctypes.c_char_p, ctypes.c_double, ctypes.c_char_p]

        def props_si(out, n1, v1, n2, v2, fluid):
            return f(out.encode(), n1.encode(), float(v1), n2.encode(), float(v2), fluid.encode())

        return ("ctypes", props_si)
    return None


def available() -> bool:
    return _impl() is not None


def props_si(output: str, name1: str, value1: float, name2: str, value2: float, fluid: str) -> float:
    impl = _impl()
    if impl is None:
        raise RuntimeError("CoolProp is not available (pip install CoolProp, or set COOLPROP_LIBRARY)")
    val = impl[1](output, name1, value1, name2, value2, FLUID_NAMES.get(fluid, fluid))
    if val != val or abs(val) > 1e300:  # NaN / HUGE_VAL signals an error in the C API
        raise ValueError(f"CoolProp failed for {output}({name1}={value1}, {name2}={value2}, {fluid})")
    return float(val)


# Convenience wrappers in the NFP unit system (bar, K, kJ/kg, kJ/(kg K), kg/m^3)
def h_pt(fluid: str, p_bar: float, T: float) -> float:
    return props_si("H", "P", p_bar * 1e5, "T", T, fluid) / 1e3


def s_pt(fluid: str, p_bar: float, T: float) -> float:
    return props_si("S", "P", p_bar * 1e5, "T", T, fluid) / 1e3


def rho_pt(fluid: str, p_bar: float, T: float) -> float:
    return props_si("D", "P", p_bar * 1e5, "T", T, fluid)


def cp_pt(fluid: str, p_bar: float, T: float) -> float:
    return props_si("C", "P", p_bar * 1e5, "T", T, fluid) / 1e3


def t_hp(fluid: str, h: float, p_bar: float) -> float:
    return props_si("T", "H", h * 1e3, "P", p_bar * 1e5, fluid)


def t_ps(fluid: str, p_bar: float, s: float) -> float:
    return props_si("T", "P", p_bar * 1e5, "S", s * 1e3, fluid)
