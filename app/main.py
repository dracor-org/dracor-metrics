"""DraCor metrics service"""

import importlib
import logging

import anyio
import networkx as nx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .models import NodeInPlayMetrics, PlayMetrics, Segments, ServiceMetadata

__version__: str = importlib.metadata.version("dracor-metrics")

# log like the errors uvicorn handles itself
logger = logging.getLogger("uvicorn.error")

# NetworkX holds the GIL, so calculating several plays at once wouldn't be
# faster but would keep all their graphs in memory at the same time.
calculation_lock = anyio.Lock()


class ErrorResponseMiddleware:
    """Answers unhandled exceptions with a 500 response

    An exception leaving the app makes uvicorn close the connection after the
    500 response of Starlette's ServerErrorMiddleware has been sent. Clients
    that have already put the connection back into their pool (like the HTTP
    client of eXist-db) then fail on their next request with no response.
    Answering with a regular response instead keeps the connection usable.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            if response_started:
                raise
            logger.exception("Unhandled error in %s %s", scope["method"], scope["path"])
            response = JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
            await response(scope, receive, send)


app = FastAPI()
app.add_middleware(ErrorResponseMiddleware)


@app.get("/")
async def root() -> ServiceMetadata:
    return ServiceMetadata(version=__version__)


@app.post("/metrics")
async def metrics(segments: Segments) -> PlayMetrics:
    """Calculates network metrics for play"""
    # Requests wait for the lock on the event loop, in order, without taking
    # a threadpool slot. The calculation runs in the threadpool, so other
    # requests are answered meanwhile (reading the request body still happens
    # on the event loop).
    async with calculation_lock:
        return await run_in_threadpool(calculate, segments)


def calculate(segments: Segments) -> PlayMetrics:
    G = nx.Graph()

    weights = {}
    for seg in segments.segments:
        # a speaker listed twice would otherwise get an edge to themselves
        speakers = list(dict.fromkeys(seg.speakers))
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
    max_degree = max([d for n, d in G.degree()], default=0)
    max_degree_ids = [n for n, d in G.degree() if d == max_degree]

    path_lengths = [y for x in nx.shortest_path_length(G) for y in x[1].values() if y > 0]

    nodes = {}
    wd = G.degree(None, "weight")
    cc = nx.closeness_centrality(G)
    bc = nx.betweenness_centrality(G)
    # Power iteration converges slowly when the graph has several components
    # with similar leading eigenvalues (e.g. kraus-die-letzten-tage-der-menschheit
    # and lermontov-strannyj-chelovek), so the default of 100 iterations isn't
    # enough. If it still fails we catch this here so we can still yield the
    # rest of the metrics.
    try:
        ec = nx.eigenvector_centrality(G, max_iter=1000) if size else {}
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
        averageDegree=(sum([d for n, d in G.degree()]) / size) if size else 0,
        averageClustering=nx.average_clustering(G) if size else 0,
        maxDegree=max_degree,
        maxDegreeIds=max_degree_ids,
        numConnectedComponents=nx.number_connected_components(G),
        numEdges=G.number_of_edges(),
        nodes=nodes,
    )
