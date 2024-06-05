# syntax=docker/dockerfile:1

FROM ubuntu AS epics-7-base

# Install general dependencies
RUN apt-get update -y && apt-get upgrade -y
RUN apt install -y git
RUN apt install -y build-essential
RUN apt install -y tree
RUN apt install -y libreadline6-dev
RUN apt install -y libtirpc-dev

# Create main EPICS folder that will hold EPICS 7 and Support
RUN mkdir EPICS 
RUN cd EPICS && git clone --recursive https://github.com/epics-base/epics-base.git
RUN cd EPICS/epics-base && make 

# Add file paths to envirorment
ENV PATH=/EPICS/epics-base/bin/linux-x86_64:${PATH}

FROM epics-7-base AS epics-7-asyn

##### Install Asyn ######################################

RUN mkdir -p EPICS/support && \
    cd /EPICS/support && \
    git clone https://github.com/epics-modules/asyn.git

RUN dpkg -L libtirpc-dev

COPY support/asyn/RELEASE /EPICS/support/asyn/configure/
RUN cat /EPICS/support/asyn/configure/RELEASE
COPY support/asyn/CONFIG_SITE /EPICS/support/asyn/configure/
RUN cat /EPICS/support/asyn/configure/CONFIG_SITE

RUN cd /EPICS/support/asyn && make

##### Install StreamDevice ##############################

FROM epics-7-asyn AS epics-7-stream

RUN cd /EPICS/support && \
    git clone https://github.com/paulscherrerinstitute/StreamDevice.git && \
    cd StreamDevice/ && rm GNUmakefile

COPY support/StreamDevice/RELEASE /EPICS/support/StreamDevice/configure/

RUN cd /EPICS/support/StreamDevice && make

###### Test the build with a simple ioc #################

FROM epics-7-stream AS epics-7-base-test

ARG testdir=/EPICS/test/testIoc

RUN mkdir -p ${testdir}
ENV PATH=/EPICS/epics-base/bin/linux-x86_64:${PATH}

# Create a simple ioc
RUN cd /EPICS/test/testIoc && \
    makeBaseApp.pl -t ioc -u pseudouser testIoc && \
    makeBaseApp.pl -i -t ioc -u pseudouser testIoc  && \
# here is where to replace the db and st.cmd files for a custom ioc
    make && \
    cd iocBoot/ioctestIoc && \
    chmod u+x st.cmd

CMD cd /EPICS/test/testIoc/iocBoot/ioctestIoc && ./st.cmd