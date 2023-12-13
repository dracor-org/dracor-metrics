# hug depends on distutils which has been removed in python 3.12
# so we are stuck with 3.11 for now
FROM python:3.11-slim

WORKDIR /dracor-metrics

COPY . .
RUN pip install poetry && poetry install

EXPOSE 8030

CMD [ "poetry", "run", "hug", "-f", "app/main.py", "-p", "8030" ]
