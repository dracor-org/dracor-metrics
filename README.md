# DraCor Metrics Service

Micro service calculating network metrics for dracor.org.

## Getting started

```bash
git clone https://github.com/dracor-org/dracor-metrics.git --branch python
cd dracor-metrics
pipenv install
pipenv run hug -f main.py
```

This runs a local development server at http://localhost:8000.

With [httpie](https://httpie.org) you can now post segment data to `/metrics`
like this:

```
$ http POST :8000/metrics 'segments:=[{"speakers": ["a", "b", "c"]}, {"speakers": ["a", "d"]}]'
HTTP/1.0 200 OK
Date: Sat, 15 Jun 2019 15:10:25 GMT
Server: WSGIServer/0.2 CPython/3.7.3
content-length: 630
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
            "eigenvector": 0.6116286437343044
        },
        "b": {
            "betweenness": 0.0,
            "closeness": 0.75,
            "degree": 2,
            "eigenvector": 0.5227204550943347
        },
        "c": {
            "betweenness": 0.0,
            "closeness": 0.75,
            "degree": 2,
            "eigenvector": 0.5227204550943347
        },
        "d": {
            "betweenness": 0.0,
            "closeness": 0.6,
            "degree": 1,
            "eigenvector": 0.28184579793865727
        }
    },
    "numConnectedComponents": 1,
    "size": 4
}
```