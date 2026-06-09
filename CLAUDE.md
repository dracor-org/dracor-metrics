# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
poetry install

# Run dev server (hot reload)
poetry run uvicorn app.main:app --reload --port 8030

# Run tests
poetry run pytest

# Run a single test
poetry run pytest tests/test_main.py::test_function_name

# Lint and format
poetry run ruff check .
poetry run ruff format .

# Docker build
docker build -t dracor/metrics .
```

## Architecture

This is a single-endpoint FastAPI microservice that computes social network metrics from dramatic plays for [dracor.org](https://dracor.org).

**The core flow:**
- `POST /metrics` accepts a list of `Segment` objects, each containing a list of speaker IDs who appear together in a scene segment
- `app/main.py` builds an undirected weighted NetworkX graph: nodes are speakers, edges are co-appearances, edge weight = number of shared segments
- NetworkX computes betweenness, closeness, and eigenvector centrality per node, plus graph-level metrics (density, diameter, average path length, clustering coefficient)
- Single-speaker segments add isolated nodes so all speakers appear in the output even with no co-appearances
- Eigenvector centrality failures (`PowerIterationFailedConvergence`) are caught and return `None` for all nodes

**Models** (`app/models.py`): `Segment` → `Segments` (input); `NodeInPlayMetrics` + `PlayMetrics` (output); `ServiceMetadata` (root endpoint).

**Releases**: Run the **Release** workflow (`release.yml`) via Actions → Run workflow, entering the new version (e.g. `1.5.3`). It bumps `version` in `pyproject.toml`, commits, tags, and opens a draft GitHub release. Edit the release notes, then publish — publishing triggers `docker-publish.yml` which builds and pushes the Docker image.

**Python version**: `.python-version` is the single source of truth. `ci.yml` reads it via `python-version-file`, `docker-publish.yml` passes it as a `--build-arg`, and the Dockerfile uses `ARG PYTHON_VERSION=3.13` as a local fallback. When upgrading Python, update `.python-version` and the `python = "~3.x"` constraint in `pyproject.toml` together.
