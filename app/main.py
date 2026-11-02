"""DraCor metrics service"""

import importlib
import logging

import networkx as nx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .models import NodeInPlayMetrics, PlayMetrics, Segments, ServiceMetadata

__version__: str = importlib.metadata.version("dracor-metrics")

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/")
async def root() -> ServiceMetadata:
    return ServiceMetadata(version=__version__)


# The DraCor API posts to /metrics/, which would otherwise be redirected.
@app.post("/metrics")
@app.post("/metrics/", include_in_schema=False)
async def metrics(segments: Segments) -> PlayMetrics:
    """Calculates network metrics for play"""

    # An exception leaving the endpoint makes uvicorn close the connection
    # after the 500 response has been sent. Clients that have already put the
    # connection back into their pool (like the HTTP client of eXist-db) then
    # fail on their next request with no response. Answering with an error
    # response instead keeps the connection usable.
    try:
        return calculate(segments)
    except Exception:
        logger.exception("Failed to calculate metrics")
        return JSONResponse(status_code=500, content={"detail": "Failed to calculate metrics"})


def calculate(segments: Segments) -> PlayMetrics:
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
    if size == 0:
        # no segment has any speakers, e.g. when no segments were found
        return PlayMetrics(
            size=0,
            density=0,
            diameter=0,
            averagePathLength=0,
            averageDegree=0,
            averageClustering=0,
            maxDegree=0,
            maxDegreeIds=[],
            numConnectedComponents=0,
            numEdges=0,
            nodes={},
        )

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
