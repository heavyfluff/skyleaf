FROM ubuntu

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update \
	&& apt install -y tzdata \
	&& apt install -y python3 \
	&& apt install -y python3-pip \
	&& apt install -y curl \
	&& apt install -y net-tools \
	&& apt install -y wget \
	&& apt install -y rabbitmq-server
RUN curl -L https://tarantool.io/RHcazFf/release/2.8/installer.sh | bash \
	&& apt install -y tarantool

RUN ulimit -n 10240
RUN pip3 install dnspython public attrs pika psycopg2-binary tarantool mail-parser urlparse2 dkimpy checkdmarc loguru pydantic

RUN mkdir /main
RUN chmod 777 /run

COPY ./main /main
COPY ./tarantool/instance/start_config.lua /etc/tarantool/instances.enabled/
COPY ./rabbitmq/conf/rabbitmq.conf /etc/rabbitmq/

#CMD cd /main;python3 -u ./main.py
CMD ["python3", "-u", "/main/main.py"]
