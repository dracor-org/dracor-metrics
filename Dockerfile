# pydantic-core/pyo3 (<=0.24.1) does not support Python 3.14
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim

WORKDIR /dracor-metrics

COPY . .
# Install the dependencies into the system Python at build time, so that the
# service also starts under an arbitrary non-root user ID (as on OpenShift/OKD,
# where a virtualenv under /root is not readable and `poetry run` fails).
RUN pip install poetry \
    && POETRY_VIRTUALENVS_CREATE=false poetry install --without dev --no-interaction \
    && rm -rf /root/.cache

# run as non-root; any user ID in group 0 works as well
USER 1001

EXPOSE 8030

CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8030" ]
