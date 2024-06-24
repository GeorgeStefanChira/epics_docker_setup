#!../../bin/linux-x86_64/exampleIoc

< envPaths

cd "${TOP}"

## Register all support components
dbLoadDatabase "dbd/exampleIoc.dbd"
exampleIoc_registerRecordDeviceDriver pdbbase

# epicsEnvSet ("STREAM_PROTOCOL_PATH", "/ioc")

## Load record instances
dbLoadRecords("db/example.db","P=user, M=:axis1, user=user")

iocInit()
