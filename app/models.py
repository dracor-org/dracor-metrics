from pydantic import BaseModel

class ServiceMetadata(BaseModel):
    service: str = "dracor-metrics"
    version: str


class Segment(BaseModel):
    speakers: list[str] = []


class Segments(BaseModel):
    segments: list[Segment]


class NodeInPlayMetrics(BaseModel):
    # Ref: https://github.com/dracor-org/dracor-api/blob/630a7504c2c12750e2437006a7bd82a794cd4399/api.yaml#L1542C9-L1542C9
    closeness: float
    betweenness: float
    degree: int
    weightedDegree: int
    eigenvector: float | None


class PlayMetrics(BaseModel):
    # Ref: https://github.com/dracor-org/dracor-api/blob/630a7504c2c12750e2437006a7bd82a794cd4399/api.yaml#L1557
    size: int
    density: float
    diameter: int
    averagePathLength: float
    averageDegree: float
    averageClustering: float
    maxDegree: int
    maxDegreeIds: list[str]
    numConnectedComponents: int
    numEdges: int
    nodes: dict[str, NodeInPlayMetrics]