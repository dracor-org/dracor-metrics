FROM python:3.12-slim

WORKDIR /dracor-metrics

COPY . .
RUN pip install poetry && poetry install --without dev

EXPOSE 8030

CMD [ "poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8030" ]
