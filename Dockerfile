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

# Create main EPICS folder that will hold EPICS 7 and Support
RUN mkdir EPICS 
RUN cd EPICS && git clone --recursive https://github.com/epics-base/epics-base.git
RUN cd EPICS/epics-base && make 

# Add file paths to envirorment
ENV PATH=/EPICS/epics-base/bin/linux-x86_64:${PATH}

FROM epics-7-base AS epics-7-modules

##### Install Modules ###################################

# make sure python exists and we create the right venv
RUN apt install -y python3-pip

COPY requirements.txt EPICS/
COPY module_installer.py EPICS/

RUN pip install --no-cache-dir --break-system-packages --upgrade pip && \
    pip install --no-cache-dir --break-system-packages -r EPICS/requirements.txt 

RUN cd EPICS/ && python3 module_installer.py

###### Test the build with a simple ioc #################

FROM epics-7-modules AS epics-7-base-test

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