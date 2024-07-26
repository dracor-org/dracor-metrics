"""DraCor metrics service"""

import importlib

import networkx as nx
from fastapi import FastAPI

from .models import NodeInPlayMetrics, PlayMetrics, Segments, ServiceMetadata

__version__: str = importlib.metadata.version("dracor-metrics")

app = FastAPI()


@app.get("/")
async def root() -> ServiceMetadata:
    return ServiceMetadata(version=__version__)


@app.post("/metrics")
async def metrics(segments: Segments) -> PlayMetrics:
    """Calculates network metrics for play"""

    G = nx.Graph()

    weights = {}
    for seg in segments.segments:
        speakers = seg.speakers
        length = len(speakers)
        # if segment has only one speaker we add her as a node to make sure she
        # is included in the graph even if she has no connections
        if length == 1:
            G.add_node(speakers[0])
        for i in range(length):
            if i < length - 1:
                source = speakers[i]
                others = speakers[i + 1 : length]
                for target in others:
                    edge = tuple(sorted((source, target)))
                    weights[edge] = weights.get(edge, 0) + 1

    G.add_weighted_edges_from([(n[0], n[1], w) for n, w in weights.items()])

    size = len(list(G.nodes))
    max_degree = max([d for n, d in G.degree()])
    max_degree_ids = [n for n, d in G.degree() if d == max_degree]

    path_lengths = [y for x in nx.shortest_path_length(G) for y in x[1].values() if y > 0]

    nodes = {}
    wd = G.degree(None, "weight")
    cc = nx.closeness_centrality(G)
    bc = nx.betweenness_centrality(G)
    # FIXME: nx.eigenvector_centrality throws an exception with
    # https://dracor.org/api/corpora/rus/play/lermontov-strannyj-chelovek
    # we catch this here so we can still yield the rest of the metrics.
    try:
        ec = nx.eigenvector_centrality(G)
    except nx.exception.PowerIterationFailedConvergence:
        ec = {}

    for n, d in G.degree():
        node_metrics = NodeInPlayMetrics(
            degree=d,
            weightedDegree=wd[n],
            betweenness=bc[n],
            closeness=cc[n],
            eigenvector=None,
        )
        nodes[n] = node_metrics
        if n in ec:
            nodes[n].eigenvector = ec[n]

    return PlayMetrics(
        size=size,
        density=nx.density(G),
        diameter=max(path_lengths) if len(path_lengths) else 0,
        averagePathLength=(sum(path_lengths) / len(path_lengths)) if len(path_lengths) else 0,
        averageDegree=sum([d for n, d in G.degree()]) / size,
        averageClustering=nx.average_clustering(G),
        maxDegree=max_degree,
        maxDegreeIds=max_degree_ids,
        numConnectedComponents=nx.number_connected_components(G),
        numEdges=G.number_of_edges(),
        nodes=nodes,
    )
