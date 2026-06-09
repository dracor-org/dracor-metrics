# pydantic-core/pyo3 (<=0.24.1) does not support Python 3.14
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim

WORKDIR /dracor-metrics

COPY . .
RUN pip install poetry && poetry install --without dev

EXPOSE 8030

CMD [ "poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8030" ]
