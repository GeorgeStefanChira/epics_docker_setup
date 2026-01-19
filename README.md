# DEPRECATED

This project as been depracted as there is no dependecies on it. Additionaly, there are other images for docker setups available.
Feel free to use the contents of this project for anything you may need.

## EPICS DOCKER SETUP

Aim of this project: to create a simple docker image for learning purposes. At the moment it's not intended to be used for any projects, but feel free to use it as a base/reference material.

You can also use the python file to install EPICS modules.

---

- [DEPRECATED](#deprecated)
  - [EPICS DOCKER SETUP](#epics-docker-setup)
  - [Quick Install](#quick-install)
  - [Contributions](#contributions)

---

## Quick Install

Since this project is mostly for learning purposes, it's not (yet) available on DockerHub.
All you need to do is install docker and build an image, then run it.

To build an image with everything:

```shell
docker build -t epics-base
```

Or to stop at a certain stage:

```shell
docker build -t epics-base --target < stage >
```

To run the Docker image, use the following line:

```shell
docker run -t -i epics-test
```

This will keep the container running and make the current shell an interactive ioc. You should see something like:

```shell
#!../../bin/linux-x86_64/exampleIoc
< envPaths
epicsEnvSet("IOC","iocexampleIoc")
epicsEnvSet("TOP","/EPICS/example/exampleIoc")
epicsEnvSet("MODULES","/EPICS/support")
epicsEnvSet("AUTOSAVE","/EPICS/support/autosave-R5-11")
epicsEnvSet("MOTOR","/EPICS/support/motor-R7-3-1")
epicsEnvSet("EPICS_BASE","/EPICS/epics-base")
cd "/EPICS/example/exampleIoc"
## Register all support components
dbLoadDatabase "dbd/exampleIoc.dbd"
exampleIoc_registerRecordDeviceDriver pdbbase
# epicsEnvSet ("STREAM_PROTOCOL_PATH", "/ioc")
## Load record instances
dbLoadRecords("db/example.db","P=user, M=:axis1, user=user")
iocInit()
Starting iocInit
############################################################################
## EPICS R7.0.8.1-DEV
## Rev. R7.0.8-44-g772c10d904c2c149ce21
## Rev. Date Git: 2024-06-19 09:38:23 -0700
############################################################################
2024/06/25 14:01:42.756 devMotorAsyn::init_record, user:axis1 connectDevice failed to "pmac"
2024/06/25 14:01:42.756 devMotorAsyn::build_trans: user:axis1 error calling queueRequest, asynManager::queueRequest asynUser not associated with a port
2024/06/25 14:01:42.756 devMotorAsyn::build_trans: user:axis1 error calling queueRequest, asynManager::queueRequest asynUser not associated with a port
iocRun: All initialization complete
epics> dbl
user:windspeed
user:liftforce
user:fanspeed
user:smoke
user:forcecalc
user:fanout01
user:axis1
```

You can also use the python file by itself on ubuntu systems. It can install several modules quite easily:

```shell
python3 module_installer < /path/to/support/dir >  < path/to/modules.yml/or/empty >
```

Read the comments in the python file for more details.

## Contributions

If you encounter any issue, feel free to report them in the issue tracker. If you have any bug fixes or extra features, please fork the repo, add your branch with the bug fix/feature and then request a merge. I'll try to reply in my free time but keep in mind this is not a priority project for me.
