import time
import random

from collections import defaultdict
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

    nodes = [node.attrib["id"]
             for node in root.findall("graphml:node", namespaces)]

    edge_list = [(e.attrib["source"], e.attrib["target"])
                 for e in root.findall("graphml:edge", namespaces)]

    if edge_default == "undirected":
        reversed_edges = [(dst, src) for src, dst in edge_list]
        edge_list += reversed_edges

    return {"nodes": nodes, "edges": edge_list}


def reduce_graph(graph, predicate):
    """Return a copy graph with a subset of nodes.

    Each node is part of the returned graph iff predicate(node) is True.

    Args:
        predicate (callable :: node -> bool)

    Returns:
        Graph: graph object.

    """

    nodes = filter(predicate, graph["nodes"])

    edge_list = [
        (src, dst) for src, dst in graph["edges"]
        if (src in nodes and dst in nodes)
    ]

    return {"nodes": nodes, "edges": edge_list}


def get_edge_map(graph):
    result = defaultdict(set)
    for src, dst in graph["edges"]:
        result[src].add(dst)
    return result


def bfs(graph, node):

    visited = {node}
    to_visit = {node}
    edge_map = get_edge_map(graph)
    distances = []

    while True:

        neighbours = set()  # neighbours of all nodes in `to_visit`

        for src in to_visit:
            neighbours = neighbours or edge_map[src]

        discovered = neighbours - visited

        if not discovered:
            break

        distances.append(len(discovered))
        to_visit = discovered
        visited = visited | discovered

    print (distances)
    return distances


def mean(nums):
    return float(sum(nums)) / max(len(nums), 1)


def calculate_asp(graph):

    mean_distances = [mean(bfs(graph, node)) for node in graph["nodes"][10:]]
    return mean(mean_distances)



def analyze_perturbation(graph, mx, nrepeats, granularity):
    """Analyze node removal purturbation.

    Run a sweep analysis, each time removing a number k of random nodes and
    calculating ASP nrepeats times.

    Maximum value of k is (mx * |nodes|)

    Args:
        - graph (graph)     : input graph
        - mx (float)        : fraction of nodes to remove
        - repeat (int)      : repeats per
        - granularity (int) : k step size

    Return:
        dictionary: k -> [asp]
    """

    def get_petrubed_asp(k):
        removed = random.sample(graph["nodes"], k)  # removed nodes
        sampled_graph = reduce_graph(graph, lambda node: node not in removed)
        return calculate_asp(sampled_graph)

    max_k = int(mx * len(graph["nodes"]))


    results = {
        k: [get_petrubed_asp(graph, k) for _ in nrepeats]
        for k in range(1, max_k, granularity)
    }

    return results


def analyze_network(graphml):

    graph = load_graphml(graphml)

    return {
        "node-count": len(graph["nodes"]),
        "edge-count": len(graph["edges"])
    }


def read_file(file):
    """Read and return content of file as a string."""
    with open(file, "r") as fid:
        return fid.read()


def main():
    file = "n2.graphml"
    graphml = read_file(file)
    graph = load_graphml(graphml)
    print(calculate_asp(graph))


if __name__ == '__main__':
    main()
