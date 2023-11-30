FROM python:3.11-slim

# WORKDIR /home/dracor
# RUN git clone https://github.com/dracor-org/dracor-metrics.git --branch python

WORKDIR /dracor-metrics

COPY . .
RUN pip install pipenv
RUN pipenv install

EXPOSE 8030

CMD [ "pipenv", "run", "hug", "-f", "main.py", "-p", "8030" ]
