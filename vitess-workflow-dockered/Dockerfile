FROM ubuntu:22.04
RUN apt update && apt upgrade
RUN apt install -y curl wget iproute2 net-tools nano
RUN apt install -y python3 python3-pip
RUN wget wget https://github.com/vitessio/vitess/releases/download/v16.0.0/vitess_16.0.0-bb768df_amd64.deb
RUN apt install -y ./vitess_16.0.0-bb768df_amd64.deb
COPY . /app
RUN pip3 install -r app/requirements.txt
CMD python3 /app/dockworkflowmon.py

