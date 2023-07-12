FROM tiangolo/uwsgi-nginx:python3.10
COPY ./requirements.txt /var/www/requirements.txt
RUN pip install pipenv
RUN pip install -r /var/www/requirements.txt