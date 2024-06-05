# @brief EPICS installer
#
# A small python script that instals EPICS modules on Ubuntu 22.04
#
import os
import subprocess
import logging
import asyncio
PIPE = subprocess.PIPE
logger = logging.getLogger(__name__)
# logger.addHandler(logging.StreamHandler())
logging.basicConfig(level=logging.DEBUG)
home_dir = "/home/gsc"


async def replace_line(file_: str = None, target_: str = None, new_line: str = None):
    """
    Searches file_ for target_ string, then replaces that line with new_line

    Args:
        file_ (_type_): _description_
        target_ (_type_): _description_
        new_line (_type_): _description_
    """
    replace = []
    try:
        with open(file_, "r+") as read_f:
            read_f.seek(0)
            for line in read_f.readlines():
                if target_ in line:
                    line = new_line
                replace.append(line)
            read_f.seek(0)
            for item in replace:
                read_f.write(item)
    except FileNotFoundError as err:
        logger.error(err)


async def git_clone(url: str = None):
    """Git clone public repos

    :param url: link to git repo
    :type url: str
    """
    process = subprocess.Popen(['git', 'clone', url],
                               cwd=f"{home_dir}/EPICS/support",
                               stdout=PIPE, stderr=PIPE)
    stdoutput, stderroutput = process.communicate()

    if 'fatal' in str(stderroutput) or 'fatal' in str(stdoutput):
        logger.error(f"stdoutput = {str(stdoutput)}, stderroutput = {str(stderroutput)}")
    else:
        logger.info(f"stdoutput = {str(stdoutput)}, stderroutput = {str(stderroutput)}")


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

    # change RELEASE to have the correct paths

    release_file = f"{home_dir}/EPICS/support/{details['dir_name']}/configure/RELEASE"
    await replace_line(release_file, "EPICS_BASE=", f"EPICS_BASE={home_dir}/EPICS/epics-base\n")
    await replace_line(release_file, "SUPPORT=", f"SUPPORT={home_dir}/EPICS/support\n")

    # change any other files (rpc for linux)

    if not details["change_files"] is None:
        for key, item in details['change_files'].items():
            release_file = f"{home_dir}/EPICS/support/{details['dir_name']}/configure/{key}"
            await replace_line(release_file, item[0], item[1])

    # make

    process = subprocess.Popen(['make'],
                               cwd=f"{home_dir}/EPICS/support/{details['dir_name']}",
                               stdout=PIPE, stderr=PIPE)
    stdoutput, stderroutput = process.communicate()

    if str(stderroutput) != "":
        logger.error(f"stdoutput = {str(stdoutput)}, stderroutput = {str(stderroutput)}")
    else:
        logger.info(f"stdoutput = {str(stdoutput)}, stderroutput = {str(stderroutput)}")


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
        "asyn": {
            "link": "https://github.com/epics-modules/asyn.git",
            "change_files": {
                    "CONFIG_SITE": ["# TIRPC=YES", " TIRPC=YES"]
                },
            "dir_name": "asyn",
            "dependencies": {}
            },
        "StreamDevice": {
            "link": "https://github.com/paulscherrerinstitute/StreamDevice.git",
            "change_files": None,
            "dir_name": "StreamDevice",
            "dependencies": {}
            },
        "seq": {
            "link": "https://github.com/ISISComputingGroup/EPICS-seq",
            "change_files": None,
            "dir_name": "EPICS-seq",
            "dependencies": {}
            },
        "motor": {
            "link": "https://github.com/epics-modules/motor",
            "change_files": None,
            "dir_name": "motor",
            "dependencies": {}
            },
        "calc": {
            "link": "https://github.com/epics-modules/calc",
            "change_files": None,
            "dir_name": "calc",
            "dependencies": {}
            },
        "autosave": {
            "link": "https://github.com/epics-modules/autosave",
            "change_files": None,
            "dir_name": "autosave",
            "dependencies": {}
            },
        "busy": {
            "link": "https://github.com/epics-modules/busy",
            "change_files": None,
            "dir_name": "busy",
            "dependencies": {}
            },
        "sscan": {
            "link": "https://github.com/epics-modules/sscan",
            "change_files": None,
            "dir_name": "sscan",
            "dependencies": {}
            },
    }
    for item in modules.keys():
        await install_module(modules[item])


if __name__ == "__main__":
    """"""
    asyncio.run(main())
