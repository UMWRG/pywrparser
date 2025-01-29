import json
import pytest

from pywrparser.types.network import PywrNetwork
from pywrparser.types.scenario import PywrScenario, PywrScenarioCombination

def test_scenarios(valid_network_file):
    """
      Two scenarios are defined
    """
    network, errors, warnings = PywrNetwork.from_file(valid_network_file)
    assert network is not None
    assert errors is None
    assert len(network.scenarios) == 2
    assert isinstance(network.scenarios[0], PywrScenario)


def test_scenario_combinations(valid_network_file):
    """
      One scenario combination is defined
    """
    network, errors, warnings = PywrNetwork.from_file(valid_network_file)
    assert network is not None
    assert errors is None
    assert len(network.scenario_combinations) == 1
    assert isinstance(network.scenario_combinations[0], PywrScenarioCombination)
