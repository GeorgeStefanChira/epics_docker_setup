# syntax=docker/dockerfile:1

FROM ubuntu AS base

# Install general dependencies
RUN apt-get update
RUN apt install -y git
RUN apt install -y build-essential
RUN apt install -y tree
RUN apt install -y libreadline6-dev

# Create main EPICS folder that will hold EPICS 7 and Support
RUN mkdir EPICS 
RUN cd EPICS && git clone --recursive https://github.com/epics-base/epics-base.git
RUN cd EPICS/epics-base && make 

# # Add file paths to envirorment
RUN echo "export PATH=/EPICS/epics-base/bin/linux-x86_64:${PATH}" >> /root/.bashrc
ENV PATH=/EPICS/epics-base/bin/linux-x86_64:${PATH}

FROM base AS EPICS7test

RUN mkdir ioc
COPY scripts/test.db ioc/

CMD softIoc -d /ioc/test.db