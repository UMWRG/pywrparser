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


def test_parameter_reference_updates():
    """
    Test that parameter references are correctly updated when parameters
    are attached to nodes. This verifies the fix for the issue where:
    1. A parameter is attached to a node attribute (ReservoirArea -> Reservoir.area)
    2. Another parameter references the attached parameter (PrecipitationVolume -> ReservoirArea)
    3. The reference should be updated to point to the canonical name (__Reservoir__:area)
    """
    network, errors, warnings = PywrNetwork.from_file("data/parameter_reference_test.json")
    assert network is not None
    assert errors is None

    # Process through the complete pipeline
    network.add_parameter_references()
    network.add_recorder_references()
    network.promote_inline_parameters()
    network.attach_reference_parameters()

    # After attach_reference_parameters:
    # - ReservoirArea should be removed from global parameters
    # - PrecipitationVolume should be in global parameters with updated reference
    assert "ReservoirArea" not in network.parameters
    assert "PrecipitationVolume" in network.parameters

    # PrecipitationVolume should now reference __Reservoir__:area instead of ReservoirArea
    precip_param = network.parameters["PrecipitationVolume"]
    assert precip_param.data["type"] == "aggregated"
    refs = precip_param.data["parameters"]
    assert "__Reservoir__:area" in refs
    assert "ReservoirArea" not in refs

    # Detach and export
    network.detach_parameters()
    exported = network.as_dict()
    params = exported.get('parameters', {})

    # Verify no broken references
    all_param_names = set(params.keys())
    for param_name, param_data in params.items():
        if param_data.get('type') == 'aggregated':
            for ref in param_data.get('parameters', []):
                assert ref in all_param_names, f"Parameter {param_name} references undefined {ref}"

    # Verify no duplicates (should have exactly one __Reservoir__:area, not both old and new names)
    reservoir_area_params = [k for k in params.keys() if 'Reservoir' in k and 'area' in k.lower()]
    assert len(reservoir_area_params) == 1, f"Expected 1 Reservoir area parameter, found {len(reservoir_area_params)}: {reservoir_area_params}"
    assert reservoir_area_params[0] == "__Reservoir__:area"
