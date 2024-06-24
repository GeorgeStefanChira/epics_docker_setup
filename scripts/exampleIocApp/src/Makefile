TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS BELOW HERE

# Use typed rset structure (see 3.16.1 release notes)
USR_CPPFLAGS += -DUSE_TYPED_RSET

# xxxRecord.h will be created from xxxRecord.dbd
DBDINC += xxxRecord

# Install xxxSupport.dbd into <top>/dbd
DBD += xxxSupport.dbd

# Build an IOC support library
LIBRARY_IOC += exampleIocSupport

# Compile and add code to the support library
exampleIocSupport_SRCS += xxxRecord.c
exampleIocSupport_SRCS += devXxxSoft.c

# Link locally-provided code into the support library,
# rather than directly into the IOC application, that
# causes problems on Windows DLL builds
exampleIocSupport_SRCS += dbSubExample.c
exampleIocSupport_SRCS += devexampleIocVersion.c
exampleIocSupport_SRCS += exampleIocHello.c
exampleIocSupport_SRCS += initTrace.c

exampleIocSupport_LIBS += $(EPICS_BASE_IOC_LIBS)

# Auto-generate a header file containing a version string.
# Version comes from the VCS if available, else date+time.
GENVERSION = exampleIocVersion.h
# Macro name
GENVERSIONMACRO = exampleIocVERSION

# Build the IOC application
PROD_IOC = exampleIoc

# exampleIoc.dbd will be created and installed
DBD += exampleIoc.dbd

# exampleIoc.dbd will include these files:
exampleIoc_DBD += base.dbd

exampleIoc_DBD += motorSupport.dbd

exampleIoc_DBD += xxxSupport.dbd
exampleIoc_DBD += dbSubExample.dbd
exampleIoc_DBD += devexampleIocVersion.dbd
exampleIoc_DBD += exampleIocHello.dbd
exampleIoc_DBD += initTrace.dbd

# exampleIoc_registerRecordDeviceDriver.cpp derives from exampleIoc.dbd
exampleIoc_SRCS += exampleIoc_registerRecordDeviceDriver.cpp

# Build the main IOC entry point where needed
exampleIoc_SRCS_DEFAULT += exampleIocMain.cpp
exampleIoc_SRCS_vxWorks += -nil-

# Link in the code from our support library
exampleIoc_LIBS += exampleIocSupport

# To build SNL programs, SNCSEQ must be defined
# in the <top>/configure/RELEASE file
ifneq ($(SNCSEQ),)
    # Build sncExample into exampleIocSupport
    sncExample_SNCFLAGS += +r
    exampleIoc_DBD += sncExample.dbd
    # A .stt sequence program is *not* pre-processed:
    exampleIocSupport_SRCS += sncExample.stt
    exampleIocSupport_LIBS += seq pv
    exampleIoc_LIBS += seq pv

    # Build sncProgram as a standalone program
    PROD_HOST += sncProgram
    sncProgram_SNCFLAGS += +m
    # A .st sequence program *is* pre-processed:
    sncProgram_SRCS += sncProgram.st
    sncProgram_LIBS += seq pv
    sncProgram_LIBS += $(EPICS_BASE_HOST_LIBS)
endif

# Link QSRV (pvAccess Server) if available
ifdef EPICS_QSRV_MAJOR_VERSION
    exampleIoc_LIBS += qsrv
    exampleIoc_LIBS += $(EPICS_BASE_PVA_CORE_LIBS)
    exampleIoc_DBD += PVAServerRegister.dbd
    exampleIoc_DBD += qsrv.dbd
endif

# Finally link IOC to the EPICS Base libraries
exampleIoc_LIBS += $(EPICS_BASE_IOC_LIBS)
exampleIoc_LIBS += motor

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD EXTRA GNUMAKE RULES BELOW HERE

# Explicit dependency needed for generated header file
devexampleIocVersion$(DEP): $(COMMON_DIR)/$(GENVERSION)
