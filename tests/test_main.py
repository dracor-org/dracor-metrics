import http.client
import json
import threading
import time

import pytest
import uvicorn
from fastapi.testclient import TestClient

from app import main
from app.main import app

client = TestClient(app)

# Ref: https://fastapi.tiangolo.com/tutorial/testing/


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "dracor-metrics"


def test_metrics():
    segments = {"segments": [{"speakers": ["a", "b", "c"]}, {"speakers": ["a", "d"]}]}
    response = client.post("/metrics", json=segments)
    assert response.status_code == 200
    expected = {
        "averageClustering": 0.5833333333333334,
        "averageDegree": 2.0,
        "averagePathLength": 1.3333333333333333,
        "density": 0.6666666666666666,
        "diameter": 2,
        "maxDegree": 3,
        "maxDegreeIds": ["a"],
        "nodes": {
            "a": {
                "betweenness": 0.6666666666666666,
                "closeness": 1.0,
                "degree": 3,
                "eigenvector": 0.6116286437343044,
                "weightedDegree": 3,
            },
            "b": {
                "betweenness": 0.0,
                "closeness": 0.75,
                "degree": 2,
                "eigenvector": 0.5227204550943347,
                "weightedDegree": 2,
            },
            "c": {
                "betweenness": 0.0,
                "closeness": 0.75,
                "degree": 2,
                "eigenvector": 0.5227204550943347,
                "weightedDegree": 2,
            },
            "d": {
                "betweenness": 0.0,
                "closeness": 0.6,
                "degree": 1,
                "eigenvector": 0.28184579793865727,
                "weightedDegree": 1,
            },
        },
        "numConnectedComponents": 1,
        "numEdges": 4,
        "size": 4,
    }
    assert response.json() == expected


@pytest.mark.parametrize("segments", [[], [{"speakers": []}, {"speakers": []}]])
def test_metrics_empty_network(segments):
    response = client.post("/metrics", json={"segments": segments})
    assert response.status_code == 200
    assert response.json() == {
        "averageClustering": 0.0,
        "averageDegree": 0.0,
        "averagePathLength": 0.0,
        "density": 0.0,
        "diameter": 0,
        "maxDegree": 0,
        "maxDegreeIds": [],
        "nodes": {},
        "numConnectedComponents": 0,
        "numEdges": 0,
        "size": 0,
    }


def test_metrics_duplicate_speakers():
    segments = {"segments": [{"speakers": ["a", "b", "a"]}, {"speakers": ["c", "c"]}]}
    response = client.post("/metrics", json=segments)
    assert response.status_code == 200
    metrics = response.json()
    assert metrics["numEdges"] == 1
    assert metrics["nodes"]["a"]["degree"] == 1
    assert metrics["nodes"]["a"]["weightedDegree"] == 1
    assert metrics["nodes"]["c"]["degree"] == 0


def test_metrics_eigenvector_slow_convergence():
    # a star and a separate path, whose leading eigenvalues are close enough
    # that power iteration needs more than the default 100 iterations
    star = [{"speakers": ["a", leaf]} for leaf in ["b", "c", "d"]]
    path = [{"speakers": pair} for pair in [["e", "f"], ["f", "g"], ["g", "h"]]]
    response = client.post("/metrics", json={"segments": star + path})
    assert response.status_code == 200
    nodes = response.json()["nodes"]
    assert all(node["eigenvector"] is not None for node in nodes.values())


@pytest.fixture
def server():
    """Run the app with uvicorn, which (unlike TestClient) handles connections"""
    # log_config=None leaves the logging setup (and caplog) alone
    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_config=None)
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started:
        assert thread.is_alive(), "server failed to start"
        assert time.monotonic() < deadline, "server didn't start in time"
        time.sleep(0.01)
    port = server.servers[0].sockets[0].getsockname()[1]
    yield port
    server.should_exit = True
    thread.join(5)


def fail_in_endpoint(segments):
    raise RuntimeError("boom")


def fail_in_response(segments):
    # fails validation of the response, after the endpoint has returned
    return {"size": "boom"}


@pytest.mark.unhandled_errors
@pytest.mark.parametrize("calculate", [fail_in_endpoint, fail_in_response])
def test_connection_usable_after_error(server, monkeypatch, caplog, calculate):
    body = json.dumps({"segments": [{"speakers": ["a", "b"]}]})
    headers = {"Content-Type": "application/json"}
    conn = http.client.HTTPConnection("127.0.0.1", server, timeout=5)
    try:
        monkeypatch.setattr(main, "calculate", calculate)
        conn.request("POST", "/metrics", body, headers)
        response = conn.getresponse()
        assert response.status == 500
        assert json.loads(response.read()) == {"detail": "Internal Server Error"}

        # the second request goes over the same connection
        monkeypatch.undo()
        conn.request("POST", "/metrics", body, headers)
        response = conn.getresponse()
        assert response.status == 200
        assert json.loads(response.read())["size"] == 2
    finally:
        conn.close()

    assert "Unhandled error in POST /metrics" in caplog.text


def post_metrics(port, speakers):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    body = json.dumps({"segments": [{"speakers": speakers}]})
    conn.request("POST", "/metrics", body, {"Content-Type": "application/json"})
    return conn


def test_metrics_concurrency(server, monkeypatch):
    started = []
    calculating = threading.Event()
    done = threading.Event()
    calculate = main.calculate

    def slow(segments):
        started.append(segments)
        calculating.set()
        done.wait(5)
        return calculate(segments)

    monkeypatch.setattr(main, "calculate", slow)
    conns = []
    try:
        conns.append(post_metrics(server, ["a", "b"]))
        assert calculating.wait(5)

        # another request is answered while the metrics are being calculated
        conns.append(http.client.HTTPConnection("127.0.0.1", server, timeout=2))
        conns[-1].request("GET", "/")
        assert conns[-1].getresponse().status == 200

        # a second calculation waits for the first one
        conns.append(post_metrics(server, ["a", "b", "c"]))
        time.sleep(0.2)
        assert len(started) == 1

        done.set()
        first, second = conns[0].getresponse(), conns[2].getresponse()
        assert first.status == 200
        assert json.loads(first.read())["size"] == 2
        assert second.status == 200
        assert json.loads(second.read())["size"] == 3
        assert len(started) == 2
    finally:
        done.set()
        for conn in conns:
            conn.close()
