import json
import pytest

from pywrparser.types.network import PywrNetwork
from pywrparser.types.parameter import PywrParameter
from pywrparser.types.recorder import PywrRecorder


def test_network_from_file_is_valid(valid_network_file):
    """
    A valid network file returns a network instance and has no errors
    """
    network, errors, warnings = PywrNetwork.from_file(valid_network_file)
    assert network is not None
    assert errors is None


def test_network_from_json_is_valid(valid_network_file):
    """
    Valid network json returns a network instance and has no errors
    """
    with open(valid_network_file, 'r') as fp:
        src = fp.read()
    network, errors, warnings = PywrNetwork.from_json(src)
    assert network is not None
    assert errors is None


def test_network_as_dict(valid_network_file):
    """
    The dict representation of a valid network contains the expected components
    """
    network, errors, warnings = PywrNetwork.from_file(valid_network_file)
    as_dict = network.as_dict()
    assert isinstance(as_dict, dict)
    components = ("metadata", "timestepper", "nodes", "edges")
    for c in components:
        assert c in as_dict


def test_network_as_json(valid_network_file):
    """
    Network is unchanged by serialisation then deserialisation
    """
    network, errors, warnings = PywrNetwork.from_file(valid_network_file)
    json_src = network.as_json()
    dict_from_json = json.loads(json_src)
    assert dict_from_json == network.as_dict()

def test_network_title(valid_network_file):
    network, errors, warnings = PywrNetwork.from_file(valid_network_file)
    assert network.title

def test_network_description(valid_network_file):
    network, errors, warnings = PywrNetwork.from_file(valid_network_file)
    assert network.metadata

def test_network_promote_inline_parameters(valid_network_file):
    network, errors, warnings = PywrNetwork.from_file(valid_network_file)
    node = network.nodes["Node_1"]
    assert isinstance(node.data["max_flow"], dict)
    network.promote_inline_parameters()
    assert isinstance(node.data["max_flow"], PywrParameter)

def test_network_detach_parameters(valid_network_file):
    network, errors, warnings = PywrNetwork.from_file(valid_network_file)
    node = network.nodes["Node_1"]
    assert isinstance(node.data["max_flow"], dict)
    network.promote_inline_parameters()
    assert isinstance(node.data["max_flow"], PywrParameter)
    network.detach_parameters()
    assert isinstance(node.data["max_flow"], str)

def test_network_add_recorder_references(valid_network_file):
    network, errors, warnings = PywrNetwork.from_file(valid_network_file)
    node = network.nodes["Node_1"]
    assert "recorder" not in node.data
    network.add_recorder_references()
    assert "recorder" in node.data

def test_network_promote_inline_recorders(valid_network_file):
    network, errors, warnings = PywrNetwork.from_file(valid_network_file)
    node = network.nodes["Node_1"]
    assert not isinstance(node.data["max_flow"], PywrRecorder)
    network.promote_inline_recorders()
    assert isinstance(node.data["max_flow"], PywrRecorder)
