FROM ubuntu:18.04

RUN apt-get update && \
        apt-get install -y software-properties-common 
RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update -y

RUN apt-get install -y build-essential python3.6 python3.6-dev python3-pip python3.6-venv && \
        apt-get install -y git

# update pip
RUN python3.6 -m pip install pip --upgrade && \
        python3.6 -m pip install wheel

RUN apt-get install -y vim
RUN apt-get install -y ssh
RUN apt-get install -y inetutils-ping 
RUN apt-get install -y telnet 
RUN apt-get install -y nano
# update version of requests library to latest
RUN pip3 install --upgrade pip
RUN pip3 uninstall -y requests
#RUN pip3 install requests
RUN pip3 uninstall -y urllib3 
RUN pip3 install urllib3
RUN pip3 install swagger_spec_validator==2.4.0
RUN pip3 install bravado
RUN pip3 install PyJWT
RUN pip3 install virtualenv
RUN pip3 install ipython
#RUN pip3 install pyaml
#RUN pip3 install coloredlogs
#RUN pip3 install -i https://test.pypi.org/simple/ ftd-api
#RUN pip3 install --extra-index-url=https://test.pypi.org/simple/ ftd-api
RUN pip3 install ftd_api
RUN echo "alias python=python3" >> ~/.bashrc
RUN ln -s /usr/bin/python3 /usr/bin/python


