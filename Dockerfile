# sticking to 3.12 for now as there are problems compiling dependencies on 3.13
FROM python:3.13.7-slim

WORKDIR /dracor-metrics

COPY . .
RUN pip install poetry && poetry install --without dev

EXPOSE 8030

CMD [ "poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8030" ]
