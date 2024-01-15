FROM python:3.12-slim

WORKDIR /dracor-metrics

COPY . .
RUN pip install poetry && poetry install

EXPOSE 8030

CMD [ "poetry", "run", "hug", "-f", "app/main.py", "-p", "8030" ]
