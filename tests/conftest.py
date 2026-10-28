import pytest

from ssme.cycle import run_cycle
from ssme.thermo import coolprop_backend


@pytest.fixture(scope="session")
def isolated():
    return run_cycle("isolated", hydrogen_table="pH2")


@pytest.fixture(scope="session")
def chained():
    return run_cycle("chained", hydrogen_table="pH2")


@pytest.fixture(scope="session")
def isolated_normal_h2():
    return run_cycle("isolated", hydrogen_table="H2")


requires_coolprop = pytest.mark.skipif(not coolprop_backend.available(), reason="CoolProp not available")
