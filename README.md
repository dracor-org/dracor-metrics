# DraCor Metrics Service

Microservice calculating network metrics for dracor.org.

*Note: dracor-metrics does not yet run with Python 3.12. Since, via hug, we
depend on distutils, which have been removed from 3.12, 3.11 is the latest
supported Python version for now.*

## Getting started

```bash
git clone https://github.com/dracor-org/dracor-metrics.git
cd dracor-metrics
pipenv install --python 3.11
pipenv run hug -f main.py -p 8030
```

This runs a local development server at http://localhost:8030.

With [httpie](https://httpie.org) you can now post segment data to `/metrics`
like this:

```
$ http POST :8030/metrics 'segments:=[{"speakers": ["a", "b", "c"]}, {"speakers": ["a", "d"]}]'
HTTP/1.0 200 OK
Date: Wed, 19 Jun 2019 14:59:16 GMT
Server: WSGIServer/0.2 CPython/3.7.3
content-length: 714
content-type: application/json; charset=utf-8

{
    "averageClustering": 0.5833333333333333,
    "averageDegree": 2.0,
    "averagePathLength": 1.3333333333333333,
    "density": 0.6666666666666666,
    "diameter": 2,
    "maxDegree": 3,
    "maxDegreeIds": [
        "a"
    ],
    "nodes": {
        "a": {
            "betweenness": 0.6666666666666666,
            "closeness": 1.0,
            "degree": 3,
            "eigenvector": 0.6116286437343044,
            "weightedDegree": 3
        },
        "b": {
            "betweenness": 0.0,
            "closeness": 0.75,
            "degree": 2,
            "eigenvector": 0.5227204550943347,
            "weightedDegree": 2
        },
        "c": {
            "betweenness": 0.0,
            "closeness": 0.75,
            "degree": 2,
            "eigenvector": 0.5227204550943347,
            "weightedDegree": 2
        },
        "d": {
            "betweenness": 0.0,
            "closeness": 0.6,
            "degree": 1,
            "eigenvector": 0.28184579793865727,
            "weightedDegree": 1
        }
    },
    "numConnectedComponents": 1,
    "numEdges": 4,
    "size": 4
}
```

## Docker

The metrics service can also be run in a docker container:

```bash
docker build -t dracor/metrics .
docker run -p 8030:8030 --rm dracor/metrics
```
