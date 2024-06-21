< envPaths

cd "${TOP}"

## Register all support components
dbLoadDatabase("dbd/example.dbd")
example_registerRecordDeviceDriver(pdbbase)

epicsEnvSet ("STREAM_PROTOCOL_PATH", "/ioc")
pmacAsynIPConfigure("geo1", "127.0.0.1:1025")
pmacCreateController("pmac", "geo1", 0, 8, 50, 500)
pmacCreateAxis("pmac", 1)

## Load record instances
dbLoadRecords("db/example.db","P=ge, M=:axis1, user=user")

iocInit()
