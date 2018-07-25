import time
from xml.etree import ElementTree as ET

def load_graphml(graphml_str):
    """Load nodes and edges from a GraphML file.

    Args:
        graphml_str (str): Content of graphml file.
    """

    tree = ET.ElementTree(ET.fromstring(graphml_str))
    root = tree.getroot()[0]
    namespaces = {"graphml": "http://graphml.graphdrawing.org/xmlns"}
    edge_default = root.attrib.get("edgedefault", "directed")

    nodes = [
        node.attrib["id"]
        for node in root.findall("graphml:node", namespaces)
    ]

    edge_list = [(e.attrib["source"], e.attrib["target"])
                 for e in root.findall("graphml:edge", namespaces)]

    if edge_default == "undirected":
        reversed_edges = [(dst, src) for src, dst in edge_list]
        edge_list += reversed_edges

    return {"nodes": nodes, "edges": edge_list}


def analyze_network(graphml):

    graph = load_graphml(graphml)

    return {
        "node-count": len(graph["nodes"]),
        "edge-count": len(graph["edges"])
    }