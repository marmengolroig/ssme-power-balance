"""SSME staged-combustion cycle model (Python port of the 2025 SSME assignment).

Quick start::

    from ssme import run_cycle
    res = run_cycle("isolated")          # component validation against the reference point
    for c in res.failed: print(c.item, c.quantity, c.computed, c.reference)
"""

from .cycle import Check, CycleResult, run_cycle, summary

__all__ = ["Check", "CycleResult", "run_cycle", "summary"]
__version__ = "0.1.0"
