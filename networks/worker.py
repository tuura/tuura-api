import time
import json
import docopt
import random

from xml.etree import ElementTree as ET
from statistics import pstdev
from collections import Counter
from collections import defaultdict


usage = """Network Analysis Worker (v0.1)

Usage:
  worker.py [options] <file.graphml>

Options:
  --max=<float>        Maximum fraction of nodes to remove [default: 0.5].
  --repeats=<int>      Repeats per data point [default: 10].
  --granularity=<int>  Step size of nodes removed [default: 2].
  --method=<str>       Node selection method [default: random]

"""


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

    nodes = [node for node in graph["nodes"] if predicate(node)]

    edge_list = [(src, dst) for src, dst in graph["edges"]
                 if (src in nodes and dst in nodes)]

    return {"nodes": nodes, "edges": edge_list}


def get_edge_map(graph):
    """Return a map: src node -> set of destinations."""
    result = defaultdict(set)
    for src, dst in graph["edges"]:
        result[src].add(dst)
    return result


def bfs(graph, root):
    """Run BFS from a root node.

    Returns:
        Number of nodes discovered in each round (list)
    """

    visited = {root}
    to_visit = {root}
    edge_map = get_edge_map(graph)
    node_counts = []

    while True:
        neighbours = set()  # neighbours of all nodes in `to_visit`
        for src in to_visit:
            neighbours.update(edge_map[src])
        discovered = neighbours - visited
        if not discovered:
            break
        node_counts.append(len(discovered))
        to_visit = discovered
        visited.update(discovered)

    return node_counts


def mean(nums):
    """Calculate mean of numbers."""
    return float(sum(nums)) / max(len(nums), 1)


def calculate_mean_asp(graph):
    """Calculate ASP of a graph."""

    def calculate_asp(root):
        """Calculate mean ASP for paths starting with root."""
        node_counts = bfs(graph, root)
        weighed = [
            node_count * distance
            for node_count, distance
            in zip(node_counts, range(1, len(node_counts)+1))
        ]
        # Note: node_counts is [] for disconnected roots
        return sum(weighed) / sum(node_counts) if node_counts else None

    node_asps = [calculate_asp(root) for root in graph["nodes"]]
    return mean([asp for asp in node_asps if asp])


def perturb(graphml, remove_max, nrepeats, granularity, method):
    """Calculate node removal perturbation statistics.

    Run a sweep analysis, each time removing k random nodes and calculating
    ASP statistics (based on `nrepeats` trials).

    Args:
        - graphml (str)      : input graph (graphml file content)
        - remove_max (float) : fraction of nodes to remove
        - nrepeats (int)     : repeats per k
        - granularity (int)  : k step size
        - method (str)       : node selection method ("random" or "outdegree")

    Maximum number of removed nodes is (remove_max * |nodes|)

    Node selection methods:
        - random    : select random k nodes
        - outdegree : select k nodes with highest outdegree (forces nrepeats=1)

    Returns:
        results (JSON object)
    """

    try:
        graph = load_graphml(graphml)
    except Exception:
        return {"error": "could not parse graphml file"}

    def select_random_nodes(graph, k):
        return random.sample(graph["nodes"], k)

    def select_most_connected(graph, k):
        outdegrees = Counter([src for src, _ in graph["edges"]])
        return [src for src, count in outdegrees.most_common(k)]

    selectors = {
        "random": select_random_nodes,
        "outdegree": select_most_connected
    }

    try:
        selector = selectors[method]
    except KeyError:
        return {
            "error": "invalid method"
        }

    def get_petrubed_asp(k):
        removed = selector(graph, k)  # pick nodes to remove
        sampled_graph = reduce_graph(graph, lambda node: node not in removed)
        return calculate_mean_asp(sampled_graph)

    max_k = int(remove_max * len(graph["nodes"]))

    if method == "outdegree":
        # Force nrepeats = 1 when selecting nodes to remove by outdegree (since
        # repeated trials return identical results).
        nrepeats = 1

    perturbed_asps = [[get_petrubed_asp(k) for _ in range(nrepeats)]
                      for k in range(1, max_k, granularity)]

    def map_asps(func):
        return [func(vals) for vals in perturbed_asps]

    return {
        "node-count": len(graph["nodes"]),
        "edge-count": len(graph["edges"]),
        "repeats": nrepeats,
        "nodes-removed": list(range(1, max_k, granularity)),
        "asp": {
            "mean": map_asps(mean),
            "min": map_asps(min),
            "max": map_asps(max),
            "std": map_asps(pstdev),
        }
    }


def read_file(file):
    """Read and return content of file as a string."""
    with open(file, "r") as fid:
        return fid.read()


def main():
    args = docopt.docopt(usage, version="v0.1")
    graphml = read_file(args["<file.graphml>"])
    method = args["--method"]
    nrepeats = int(args["--repeats"])
    remove_max = float(args["--max"])
    granularity = int(args["--granularity"])
    results = perturb(graphml, remove_max, nrepeats, granularity, method)
    print(json.dumps(results, indent=4))


if __name__ == '__main__':
    main()
