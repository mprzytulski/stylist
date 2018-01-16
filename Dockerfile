FROM "946211468949.dkr.ecr.eu-west-1.amazonaws.com/docker-images/python3:latest"

COPY requirements.txt /var/tmp/

RUN pip install -r /var/tmp/requirements.txt && rm /var/tmp/requirements.txt

ADD . /app

COPY requirements.txt /app

RUN pip install -r /app/requirements.txt

CMD python setup.py install
