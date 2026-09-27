from pathlib import Path

import numpy as np
import pytest

from irrae.modelo import carregar_config

CONFIG = Path(__file__).resolve().parents[2] / "irrae" / "config"


@pytest.fixture(scope="session")
def cfg():
    return carregar_config(CONFIG)


@pytest.fixture(scope="session")
def tax(cfg):
    return cfg["taxonomia"]


@pytest.fixture
def rng():
    return np.random.default_rng(123)
