# pydantic-core/pyo3 (<=0.24.1) does not support Python 3.14
ARG PYTHON_VERSION=3.13

# Build stage: install the locked dependencies and the app (as a wheel) into a
# standalone virtualenv, so that poetry itself does not end up in the image.
FROM python:${PYTHON_VERSION}-slim AS builder

ARG POETRY_VERSION=2.5.1
ENV PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry-cache \
    VIRTUAL_ENV=/opt/venv

RUN pip install "poetry==${POETRY_VERSION}" && python -m venv ${VIRTUAL_ENV}

WORKDIR /dracor-metrics
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev --no-root

COPY README.md ./
COPY app ./app
RUN poetry build --format wheel \
    && ${VIRTUAL_ENV}/bin/pip install --no-deps dist/*.whl

# Runtime stage: everything lives in /opt/venv, which is world-readable, so the
# service runs under any non-root user ID (as assigned e.g. by OpenShift/OKD).
FROM python:${PYTHON_VERSION}-slim

COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:${PATH}

USER 1001

EXPOSE 8030

CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8030" ]
