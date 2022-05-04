import logging

from collections import Counter
from functools import partialmethod

from pywrparser.parsers import PywrJSONParser

from pywrparser.types import (
    PywrParameter,
    PywrRecorder
)
from pywrparser.types.exceptions import PywrParserException

from pywrparser.utils import (
    canonical_name,
    parse_reference_key
)

log = logging.getLogger(__name__)


class PywrNetwork():

    def __init__(self, parser):
        self.metadata = parser.metadata
        self.timestepper = parser.timestepper
        self.scenarios = parser.scenarios
        self.tables = parser.tables
        self.nodes = parser.nodes
        self.edges = parser.edges
        self.parameters = parser.parameters
        self.recorders = parser.recorders

    @classmethod
    def from_file(cls, filename, raise_on_parser_error=False,
                  raise_on_parser_warning=False, allow_duplicate_edges=True,
                  ruleset=None):
        try:
            with open(filename, 'r') as fp:
                json_src = fp.read()
        except OSError as err:
            err_txt = f"Unable to read input file: {err}"
            log.error(err_txt)
            exc = PywrParserException(err_txt)
            if raise_on_parser_error:
                raise exc from None
            else:
                return None, {"network": [exc]}, None

        try:
            parser = PywrJSONParser(json_src, ruleset)
        except PywrParserException as exc:
            if raise_on_parser_error:
                raise exc from None
            else:
                return None, {"network": [exc]}, None

        parser.parse(raise_on_error=raise_on_parser_error,
                     raise_on_warning=raise_on_parser_warning,
                     allow_duplicate_edges=allow_duplicate_edges)
        ret_warnings = parser.warnings if parser.has_warnings else None
        if parser.has_errors:
            return None, parser.errors, ret_warnings

        return cls(parser), None, parser.warnings

    @classmethod
    def from_json(cls, json_src, raise_on_parser_error=False,
                  raise_on_parser_warning=False, allow_duplicate_edges=True):
        parser = PywrJSONParser(json_src)
        parser.parse(raise_on_error=raise_on_parser_error,
                     raise_on_warning=raise_on_parser_warning,
                     allow_duplicate_edges=allow_duplicate_edges)
        ret_warnings = parser.warnings if parser.has_warnings else None
        if parser.has_errors:
            return None, parser.errors, ret_warnings

        return cls(parser), None, parser.warnings


    def as_dict(self):
        network = {
            "metadata": self.metadata.as_dict(),
            "timestepper": self.timestepper.as_dict(),
            "nodes": [node.as_dict() for node in self.nodes.values()],
            "edges": [edge.as_dict() for edge in self.edges]
        }
        if len(self.parameters) > 0:
            network["parameters"] = {n: p.as_dict() for n, p in self.parameters.items()}

        if len(self.recorders) > 0:
            network["recorders"] = {n: r.as_dict() for n, r in self.recorders.items()}

        if len(self.scenarios) > 0:
            network["scenarios"] = [s.as_dict() for s in self.scenarios]

        if len(self.tables) > 0:
            network["tables"] = {n: t.as_dict() for n, t in self.tables.items()}

        return network


    def as_json(self):
        import json
        return json.dumps(self.as_dict(), indent=2)


    def validate(self):
        """
          Additional network-level semantic validation, e.g..
           - Unconnected nodes
           - Unused parameters
           - Optionally: Duplicate edges
        """
        pass


    def attach_parameters(self):
        """
            1. Any values of attrs in a node which resolve to a global
               parameter are replaced with the instance of that parameter
               and the parameter is removed from the set of global parameters.

            2. Any values of attrs in a node which can be interpreted as
               an inline (i.e. dict) parameter definition are instantiated
               as parameters and the attr value replaced with the instance.
        """
        exclude = ("name", "type")
        for node in self.nodes.values():
            for attr, value in node.data.items():
                if attr.lower() in exclude:
                    """ A param could exist with the same name as a node,
                        leading to node["name"] = param
                    """
                    continue
                if isinstance(value, str):
                    param = self.parameters.get(value)
                    if not param:
                        continue
                    print(f"Attaching global param ref: {value}")
                    node.data[attr] = param
                    del self.parameters[value]
                elif isinstance(value, dict):
                    type_key = value.get("type")
                    if not type_key or "recorder" in type_key.lower():
                        continue
                    param_name = canonical_name(node.name, attr)
                    print(f"Creating inline param: {param_name}")
                    if param_name in self.parameters:
                        # Node inline param has same name as global param
                        raise ValueError("inline dups global param")
                    param = PywrParameter(param_name, value)
                    node.data[attr] = param



    def __add_component_references(self, component=None):
        """
            Where a parameter or recorder name is in the format "__nodename__:attrname"
            it is interpreted as representing the attr "attrname" on node "nodename".
            In this case, a reference to the global parameter or recorder is added to
            the node where this is not already present.

            This method should be invoked only through the partialmethod descriptors
            defined below.
        """

        component_map = {
            "parameter": self.parameters,
            "recorder" : self.recorders
        }

        # Prevent use without partial filled
        if not component:
            return

        # Prevent unorthodox use
        if component not in component_map:
            return

        store = component_map[component]

        for comp_name in store:
            try:
                node_name, attr = parse_reference_key(comp_name)
            except ValueError:
                # comp_name not in std format
                log.debug(f"Not in std format: {comp_name}")
                continue

            if node_name not in self.nodes:
                # node implied by comp_name does not exist
                log.debug(f"No such node: {comp_name} -> {node_name}")
                continue

            node = self.nodes[node_name]

            if attr in node.attrs:
                # node exists but already has implied attr
                log.debug(f"Node {node.name} already has attr: {attr}")
                continue

            # node exists, does not have attr, so create as param_name str
            log.debug(f"add_{component}_references {node.name}:{attr} -> {comp_name}")
            node.data[attr] = comp_name

    add_parameter_references = partialmethod(
            __add_component_references,
            component="parameter"
    )

    add_recorder_references = partialmethod(
            __add_component_references,
            component="recorder"
    )

    def detach_parameters(self):
        for node in self.nodes.values():
            for attr, value in node.data.items():
                if isinstance(value, PywrParameter):
                    if value.name in self.parameters:
                        # Attr param name duplicates global param name
                        raise ValueError("Attr param name duplicates global param name")
                    self.parameters[value.name] = value
                    node.data[attr] = value.name


    def detach_recorders(self):
        for node in self.nodes.values():
            for attr, value in node.data.items():
                if isinstance(value, PywrRecorder):
                    if value.name in self.recorders:
                        # Attr recorder name duplicates global recorder name
                        raise ValueError("Attr recorder name duplicates global recorder name")
                    self.recorders[value.name] = value
                    node.data[attr] = value.name


    def report(self):
        report = {
            "nodes": len(self.nodes),
            "edges": len(self.edges)
        }

        components = ("parameters", "recorders", "tables", "scenarios")

        for component in components:
            store = getattr(self, component)
            if (count := len(store)) > 0:
                report[component] = count

        return report


    @property
    def duplicate_edges(self):
        """
            Return a dict of "duplicate" edges, that is edges of length n
            comprised of the same n nodes in the same order which are
            defined more than once.
            This is permitted by Pywr but may indicate a malformed network
            in some enviroments.
        """
        edge_count = Counter((n1, n2) for (n1, n2) in self.edges)
        return {edge: count for edge, count in edge_count.items() if count > 1}
