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
RUN pip3 install requests
RUN pip3 uninstall -y urllib3 
RUN pip3 install urllib3
RUN pip3 install swagger_spec_validator==2.4.0
RUN pip3 install bravado
RUN pip3 install PyJWT
RUN pip3 install virtualenv
RUN pip3 install ipython
RUN pip3 install pyaml
RUN pip3 install coloredlogs
#RUN mkdir /code
#COPY code /code/

#ARG FTD_ANSIBLE_VERSION=v0.2.1
#ARG FTD_ANSIBLE_FOLDER=ftd-ansible

#RUN wget https://github.com/CiscoDevNet/FTDAnsible/archive/${FTD_ANSIBLE_VERSION}.tar.gz && \
#    tar -xvf ${FTD_ANSIBLE_VERSION}.tar.gz

#RUN mkdir /${FTD_ANSIBLE_FOLDER}/ && \
#    export FTD_SOURCE_FOLDER=`find ./ -maxdepth 1 -type d -name '*FTDAnsible-*'` && \
#    mv $FTD_SOURCE_FOLDER/httpapi_plugins /${FTD_ANSIBLE_FOLDER} && \
#    mv $FTD_SOURCE_FOLDER/library /${FTD_ANSIBLE_FOLDER} && \
#    mv $FTD_SOURCE_FOLDER/module_utils /${FTD_ANSIBLE_FOLDER} && \
#    mv $FTD_SOURCE_FOLDER/requirements.txt /${FTD_ANSIBLE_FOLDER} && \
#    mv $FTD_SOURCE_FOLDER/ansible.cfg  /${FTD_ANSIBLE_FOLDER}

#RUN pip install --no-cache-dir -r /${FTD_ANSIBLE_FOLDER}/requirements.txt

#ENV PYTHONPATH="$PYTHONPATH:/${FTD_ANSIBLE_FOLDER}/"
#WORKDIR /${FTD_ANSIBLE_FOLDER}

#RUN echo "export PYTHONPATH=$PYTHONPATH:/code" >> ~/.bashrc
RUN echo "alias python=python3" >> ~/.bashrc
#RUN mkdir -p /ftd-ansible/playbooks
#COPY playbooks /ftd-ansible/playbooks
#RUN mkdir -p /etc/ansible
#COPY hosts /etc/ansible/hosts
#symlink python
RUN ln -s /usr/bin/python3 /usr/bin/python
#RUN cp /ftd-ansible/module_utils/* /usr/local/lib/python3.6/dist-packages/ansible/module_utils/network/ftd/
#RUN cp /ftd-ansible/httpapi_plugins/* /usr/local/lib/python3.6/dist-packages/ansible/plugins/httpapi/
#RUN cp /ftd-ansible/library/* /usr/local/lib/python3.6/dist-packages/ansible/modules/network/ftd/
#RUN cp /ftd-ansible/ansible.cfg /etc/ansible/
#RUN sed -i 's/\.\//\/ftd-ansible\//' /etc/ansible/ansible.cfg


