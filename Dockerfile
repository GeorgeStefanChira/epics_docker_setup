# syntax=docker/dockerfile:1

FROM ubuntu AS epics-7-base

# Install general dependencies
RUN apt-get update -y && apt-get upgrade -y
RUN apt install -y git
RUN apt install -y build-essential
RUN apt install -y tree
RUN apt install -y libreadline6-dev
RUN apt install -y libtirpc-dev
RUN apt install -y re2c
RUN apt install -y libpcre3 libpcre3-dev

# Create main EPICS folder that will hold EPICS 7 and Support
RUN mkdir EPICS 
RUN cd EPICS && git clone --recursive https://github.com/epics-base/epics-base.git
RUN cd EPICS/epics-base && make 

# Add file paths to envirorment
ENV PATH=/EPICS/epics-base/bin/linux-x86_64:${PATH}

FROM epics-7-base AS epics-7-modules

##### Install Modules ###################################

# make sure python exists and we install the dependencies
RUN apt install -y python3-pip

COPY requirements.txt EPICS/
COPY module_installer.py EPICS/
COPY modules.yml EPICS/

RUN pip install --no-cache-dir --break-system-packages -r EPICS/requirements.txt 

RUN cd EPICS/ && python3 module_installer.py 

###### Test the build with a simple ioc #################

# FROM epics-7-modules AS epics-7-base-test

ARG testdir=/EPICS/example/exampleIoc

RUN mkdir -p ${testdir}
ENV PATH=/EPICS/epics-base/bin/linux-x86_64:${PATH}

# Create a simple ioc
RUN cd /EPICS/example/exampleIoc && \
    makeBaseApp.pl -t example -u user exampleIoc && \
    makeBaseApp.pl -i -t example -u user exampleIoc

# Replace the ioc files
COPY scripts/configure/RELEASE EPICS/example/exampleIoc/configure
COPY scripts/db/example.db EPICS/example/exampleIoc/db
COPY scripts/exampleIocApp/Db/Makefile EPICS/example/exampleIoc/exampleIocApp/Db/Makefile
COPY scripts/exampleIocApp/src/Makefile EPICS/example/exampleIoc/exampleIocApp/src/Makefile
COPY scripts/iocBoot/iocexampleIoc/startExample.cmd EPICS/example/exampleIoc/iocBoot/iocexampleIoc/startExample.cmd

RUN cd $EPICS && ls
RUN cd /EPICS/support && ls
RUN cd /EPICS/support/motor-R7-3-1 && ls
RUN cd /EPICS/support/busy-R1-7-4 && ls
RUN cd /EPICS/support/busy-R1-7-4/dbd && ls
RUN cd /EPICS/support/motor-R7-3-1/dbd && ls
RUN cd /EPICS/example && tree


RUN cd /EPICS/example/exampleIoc && \
    make && \
    cd iocBoot/iocexampleIoc && \
    chmod u+x startExample.cmd

CMD cd /EPICS/example/exampleIoc/iocBoot/iocexampleIoc && ./startExample.cmd