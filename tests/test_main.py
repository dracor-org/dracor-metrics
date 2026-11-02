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


def test_metrics_trailing_slash():
    segments = {"segments": [{"speakers": ["a", "b"]}]}
    response = client.post("/metrics/", json=segments, follow_redirects=False)
    assert response.status_code == 200
    assert response.json()["size"] == 2


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


@pytest.fixture
def server():
    """Run the app with uvicorn, which (unlike TestClient) handles connections"""
    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="critical")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.01)
    port = server.servers[0].sockets[0].getsockname()[1]
    yield port
    server.should_exit = True
    thread.join()


def test_connection_usable_after_error(server, monkeypatch, caplog):
    def fail(segments):
        raise RuntimeError("boom")

    body = json.dumps({"segments": [{"speakers": ["a", "b"]}]})
    headers = {"Content-Type": "application/json"}
    conn = http.client.HTTPConnection("127.0.0.1", server)

    monkeypatch.setattr(main, "calculate", fail)
    conn.request("POST", "/metrics", body, headers)
    response = conn.getresponse()
    response.read()
    assert response.status == 500

    # the second request goes over the same connection
    monkeypatch.undo()
    conn.request("POST", "/metrics", body, headers)
    response = conn.getresponse()
    assert response.status == 200
    assert json.loads(response.read())["size"] == 2
    conn.close()

    assert "Failed to calculate metrics" in caplog.text
