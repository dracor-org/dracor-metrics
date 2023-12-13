import hug
from falcon import HTTP_200

from app import main


def test_metrics():
    segments = {"segments": [{"speakers": ["a", "b", "c"]}, {"speakers": ["a", "d"]}]}
    response = hug.test.post(main, "metrics", segments)
    assert response.status == HTTP_200
    expected = {
        "averageClustering": 0.5833333333333333,
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
    assert response.data == expected
