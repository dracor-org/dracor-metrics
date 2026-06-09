# DraCor Metrics Service

Microservice calculating network metrics for dracor.org.

## Getting started

```bash
git clone https://github.com/dracor-org/dracor-metrics.git
cd dracor-metrics
poetry install
poetry run pytest
poetry run uvicorn app.main:app --reload --port 8030
```

This runs a local development server at http://localhost:8030.

With [httpie](https://httpie.org) you can now post segment data to `/metrics`
like this:

```
$ http POST :8030/metrics 'segments:=[{"speakers": ["a", "b", "c"]}, {"speakers": ["a", "d"]}]'
HTTP/1.1 200 OK
content-length: 665
content-type: application/json
date: Fri, 26 Jul 2024 19:24:55 GMT
server: uvicorn

{
    "averageClustering": 0.5833333333333334,
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
docker pull dracor/metrics
docker run -p 8030:8030 --rm dracor/metrics
```

## Releasing

1. Go to **Actions → Release → Run workflow** and enter the new version number (e.g. `1.5.3`)
2. The workflow bumps the version in `pyproject.toml`, commits, tags, and opens a draft GitHub release
3. Edit the release notes and click **Publish release**
4. Publishing triggers the Docker build and pushes the new image to DockerHub as `dracor/metrics`

## License

dracor-metrics is [MIT licensed](./LICENSE).
