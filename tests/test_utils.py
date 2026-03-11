import pytest
from pywrparser.utils import (
    canonical_name,
    parse_reference_key
)

@pytest.mark.parametrize(
    ("name_title", "input_text", "expected"), [
        ("SIMPLE_CANONICAL", "__node__:attr", ("node", "attr") ),
        ("COMPLEX_CANONICAL", "__node extended(v2)__:attr name", ("node extended(v2)", "attr name")),
        ("NUMERIC_ROUTE_NAME", "__27 Bulls Green to Sacombe__:MSE", ("27 Bulls Green to Sacombe", "MSE")),
        ("BOOSTER_WITH_COMMAS", "__Hadham Mill Booster 5, 6, 7__:simulated_flow", ("Hadham Mill Booster 5, 6, 7", "simulated_flow")),
        ("PLUS_SIGN_IN_NAME", "__Dennis Ln + A41 Valves__:simulated_flow", ("Dennis Ln + A41 Valves", "simulated_flow")),
        ("BRACKETED_NAME", "__Grafham [AWS]__:simulated_flow", ("Grafham [AWS]", "simulated_flow")),
        ("QUOTED_DIAMETER_PREFIX", "__12\" Hunton Bridge to Adeyfield__:MSE", ("12\" Hunton Bridge to Adeyfield", "MSE")),
        ("QUOTED_SUFFIX", "__Mark Hall 7\"__:simulated_flow", ("Mark Hall 7\"", "simulated_flow"))
    ]
)
def test_parse_valid_names(name_title, input_text, expected):
    """
    Are references in canonical format correctly parsed?
    """
    assert parse_reference_key(input_text) == (expected[0], expected[1])


def test_parse_rejects_unsupported_punctuation():
    with pytest.raises(ValueError):
        parse_reference_key("__name!__:attr")


@pytest.mark.parametrize(
    ("input_node", "input_attr", "expected"), [
        ("node", "attr", "__node__:attr")
    ]
)
def test_canonical_names(input_node, input_attr, expected):
    """
    Are references correctly generated in canonical format?
    """
    assert canonical_name(input_node, input_attr) == expected
