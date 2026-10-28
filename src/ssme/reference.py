"""Access to the SSME reference data (``ssme/data/ssme_reference.yaml``)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from .streams import FluidStream
from .thermo.fluids import RealFluid


@dataclass(frozen=True)
class Reference:
    raw: dict[str, Any]
    hydrogen_table: str = "pH2"
    backend: str = "nfp"  # real-fluid property backend: "nfp" (NIST tables) or "coolprop"

    @property
    def stations(self) -> dict[str, dict]:
        return self.raw["stations"]

    @property
    def components(self) -> dict[str, dict]:
        return self.raw["components"]

    @property
    def shafts(self) -> dict[str, dict]:
        return self.raw["shafts"]

    @property
    def acceptance(self) -> dict[str, float]:
        return self.raw["acceptance"]

    def st(self, name: str) -> dict:
        return self.stations[name]

    def value(self, station: str, key: str, default=None):
        return self.stations[station].get(key, default)

    def fluid(self, station: str) -> RealFluid:
        f = self.stations[station]["fluid"]
        if f == "H2":
            return RealFluid(self.hydrogen_table, self.backend)
        if f == "O2":
            return RealFluid("O2", self.backend)
        raise KeyError(f"{station} is a gas-mixture station; it has no single real fluid")

    def has_state(self, station: str) -> bool:
        s = self.stations[station]
        return "P" in s and "T" in s

    def stream(self, station: str) -> FluidStream:
        """Reference state of a real-fluid station as a stream."""
        s = self.stations[station]
        return FluidStream(self.fluid(station), s["m_dot"], s["P"], s["T"])


@cache
def _load_yaml(path: str | None) -> dict:
    if path is None:
        text = resources.files("ssme.data").joinpath("ssme_reference.yaml").read_text()
    else:
        text = Path(path).read_text()
    return yaml.safe_load(text)


def load_reference(
    path: str | Path | None = None, *, hydrogen_table: str | None = None, backend: str = "nfp"
) -> Reference:
    raw = _load_yaml(str(path) if path is not None else None)
    table = hydrogen_table or raw.get("meta", {}).get("hydrogen_table", "pH2")
    if table not in ("pH2", "H2"):
        raise ValueError("hydrogen_table must be 'pH2' (para) or 'H2' (normal)")
    return Reference(raw, table, backend)
