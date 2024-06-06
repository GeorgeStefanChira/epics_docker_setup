# @brief EPICS installer
#
# A small python script that instals EPICS modules on Ubuntu 22.04
#
# TODO:
#   - add a file that keeps track of installs
#   - move the modules dict so that we can reference other modules (for dependency management)
#   - check operation time for each function
#   - move git cloning outside install_modules method. As of now, async doesn't help much this way

import os
import subprocess
import logging
import asyncio

PIPE = subprocess.PIPE
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
home_dir = ""


def replace_line(file_: str = None, replace: dict = None):
    """
    Searches file_ and use replace dictionary to change lines

    Opens a file, reads the lines, makes a backup copy, and then replaces the lines according to
    the replace dict.

    Args:
        file_ (str): Path to file
        replace (dict): {'old line / string we look for' : 'new line to insert in place'}
    """
    # open file and save lines in a list
    try:
        f = open(file_, 'r')
        lines = f.readlines()
        f.close()
    except FileNotFoundError as err:
        logger.error(err)
        return

    new_file_as_list = []
    for line in lines:
        current_line = line
        for old_line, new_line in replace.items():
            if old_line in line:
                # easiest to just replace the line
                current_line = new_line
        new_file_as_list.append(current_line)

    # Create a backup
    f = open(f"{file_}.backup", 'w')
    f.writelines(lines)
    f.close()

    # Overwrite the old one
    f = open(file_, 'w')
    f.writelines(new_file_as_list)
    f.close()


async def git_clone(url: str = None):
    """Git clone public repos
    """
    process = subprocess.Popen(['git', 'clone', url],
                               cwd=f"{home_dir}/EPICS/support",
                               stdout=PIPE, stderr=PIPE)
    stdoutput, stderroutput = process.communicate()

    if 'fatal' in str(stderroutput) or 'fatal' in str(stdoutput):
        logger.error(f"cloning {url} encountered error =========")
        raise ValueError("BAD")
        # logger.error(f"stdoutput = {str(stdoutput)}, stderroutput = {str(stderroutput)}")
    # else:
        # logger.info(f"stdoutput = {str(stdoutput)}, stderroutput = {str(stderroutput)}")


async def install_module(details: dict = None):
    """
    Instals EPICS modules

    Args:
        dependencies (list, optional): Strings of dependencies names.
                                       Defaults to None.
    """
    # check dependencies
    dependencies = details["dependencies"]
    for key, item in dependencies.items():
        if not os.path.isdir(f"/{home_dir}/EPICS/support/{key}"):
            # do a bit of recursion
            await install_module(item)

    # check if it already exists
    # if not os.path.isdir(f"/{home_dir}/EPICS/support/{details['dir_name']}"):

    # git pull library
    await git_clone(details["link"])

    # all RELEASE files start with wrong paths for epics. Add this here:

    release_file = f"{home_dir}/EPICS/support/{details['dir_name']}/configure/RELEASE"

    replace_dict = details['change_files']
    replace_dict['configure/RELEASE']["EPICS_BASE="] = f"EPICS_BASE={home_dir}/EPICS/epics-base\n"
    replace_dict['configure/RELEASE']["SUPPORT="] = f"SUPPORT={home_dir}/EPICS/support\n"

    # Change files

    # the 'change_files' entry is a set of keys and dictionaries. The key is the path to the file
    # from the module folder, the dictionary pairs any line we want to replace with the new line
    # so the form is:

    # 'path to file' : {
    #                       'old line / string we look for' : 'new line to insert in place'
    #                   }

    for file_name, line_to_replace in replace_dict.items():

        release_file = f"{home_dir}/EPICS/support/{details['dir_name']}/{file_name}"
        replace_line(release_file, line_to_replace)

    # make

    process = subprocess.Popen(['make'],
                               cwd=f"{home_dir}/EPICS/support/{details['dir_name']}",
                               stdout=PIPE, stderr=PIPE)
    stdoutput, stderroutput = process.communicate()

    if 'Error 2' in str(stderroutput):
        logger.error(f"during make: {details['dir_name']} encountered error =========")
        # logger.error(f"stderroutput = {str(stderroutput)}")
    else:
        logger.info(f"Successfully ran make for {details['dir_name']}")
        # logger.info(f"stdoutput = {str(stdoutput)}, stderroutput = {str(stderroutput)}")


async def main():
    # entry point
    # check that the file structure exists:
    if not os.path.isdir(f"{home_dir}/EPICS"):
        logger.warning("EPICS directory could not be found, \
                       creating EPICS directory")
        os.mkdir(f"{home_dir}/EPICS")
    if not os.path.isdir(f"{home_dir}/EPICS/support"):
        logger.warning("EPICS/support directory could not be found, \
                       creating EPICS/support directory")
        os.mkdir(f"{home_dir}/EPICS/support")

    modules = {
        "seq": {
            "link": "https://github.com/ISISComputingGroup/EPICS-seq",
            "change_files": {"configure/RELEASE": {
                            "include $(TOP)/../../../ISIS_CONFIG": "",
                            "-include $(TOP)/../../../ISIS_CONFIG.$(EPICS_HOST_ARCH)": ""}},
            "dir_name": "EPICS-seq",
            "dependencies": {}
            },
        "sscan": {
            "link": "https://github.com/epics-modules/sscan",
            "change_files": {"configure/RELEASE": {"SNCSEQ=": "SNCSEQ=$(SUPPORT)/EPICS-seq\n"}},
            "dir_name": "sscan",
            "dependencies": {}
            },
        "ipac": {
            "link": "https://github.com/epics-modules/ipac",
            "change_files": {"configure/RELEASE": {}},
            "dir_name": "ipac",
            "dependencies": {}
            },
        "autosave": {
            "link": "https://github.com/epics-modules/autosave",
            "change_files": {"configure/RELEASE": {}},
            "dir_name": "autosave",
            "dependencies": {}
            },
        "calc": {
            "link": "https://github.com/epics-modules/calc",
            "change_files": {"configure/RELEASE": {"SSCAN=": "SSCAN=$(SUPPORT)/sscan\n",
                                                   "#SNCSEQ=": "SNCSEQ=$(SUPPORT)/EPICS-seq\n"
                                                   }},
            "dir_name": "calc",
            "dependencies": {}
            },
        "asyn": {
            "link": "https://github.com/epics-modules/asyn.git",
            "change_files": {
                    "configure/RELEASE": {"#CALC=": "CALC=$(SUPPORT)/calc\n",
                                          "#SSCAN=": "SSCAN=$(SUPPORT)/sscan\n",
                                          "#SNCSEQ=": "SNCSEQ=$(SUPPORT)/EPICS-seq\n"},
                    "configure/CONFIG_SITE": {"# TIRPC=YES": " TIRPC=YES"}
                },
            "dir_name": "asyn",
            "dependencies": {}
            },
        "busy": {
            "link": "https://github.com/epics-modules/busy",
            "change_files": {"configure/RELEASE": {"ASYN=": "ASYN=$(SUPPORT)/asyn\n",
                                                   "AUTOSAVE=": "AUTOSAVE=$(SUPPORT)/autosave\n",
                                                   "BUSY=": "BUSY=$(SUPPORT)/busy\n"
                                                   }},
            "dir_name": "busy",
            "dependencies": {}
            },
        "StreamDevice": {
            "link": "https://github.com/paulscherrerinstitute/StreamDevice.git",
            "change_files": {"configure/RELEASE": {"ASYN=": "ASYN=$(SUPPORT)/asyn\n",
                                                   "CALC=": "CALC=$(SUPPORT)/calc\n",
                                                   "PCRE=": "PCRE_INCLUDE=/usr/include/pcre\n\
                                                   PCRE_LIB=/usr/lib64\n"}},
            "dir_name": "StreamDevice",
            "dependencies": {}
            },
        "motor": {
            "link": "https://github.com/epics-modules/motor",
            "change_files": {"configure/RELEASE": {"ASYN=": "ASYN=$(SUPPORT)/asyn\n",
                                                   "SNCSEQ=": "SNCSEQ=$(SUPPORT)/EPICS-seq\n",
                                                   "BUSY=$": "BUSY=$(SUPPORT)/busy\n",
                                                   "IPAC=$": "IPAC=$(SUPPORT)/ipac\n"
                                                   }},
            "dir_name": "motor",
            "dependencies": {}
            },
    }
    for item in modules.keys():
        await install_module(modules[item])


if __name__ == "__main__":
    """"""
    asyncio.run(main())
