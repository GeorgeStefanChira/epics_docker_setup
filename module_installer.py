# @brief EPICS installer
#
# A small python script that instals EPICS modules on Ubuntu 22.04
# Takes two arguments:
#
# path to install directory
# path to modules.yml file
# TODO:
#   - add a file that keeps track of installs
#   - move the modules dict so that we can reference other modules (for dependency management)

import os
import sys
import yaml
import requests
import tarfile
import subprocess
import logging
import asyncio


class EPICS_module_installer:
    """
    # Installs EPICS modules using a yml file

    ## Yaml file format

    ----------------

    nickname-of-the-module:
        name: "This is the string used in RELEASE files as a path variable"
        version: "Version string as it appears in the link"
        binary: "link to download the binary"
        git: "link to git repo" (this is only used when binary link doesn't exist)
        dependency: "other EPICS modules this depends on"
            - nickname of dependency 1
            - nickname of dependency 2
            - nickname of dependency 3
        add_to_file:
            CONFIG_SITE:
                - "Line to be added to CONFIG_SITE.local"
            RELEASE:
                - "Line to be added to RELEASE.local"

    ----------------

    Nickname is used in folder names and when specifying other modules as dependencies

    The name must always be the string used by other modules as a path file.

    Version is required for binary installs but will be ignored when using git cloning.

    Only CONFIG_SITE and RELEASE are parsed when adding extra lines to files.
    """

    def __init__(self, install_path: str, modules_file: str) -> None:
        """
        Reads a yml file and installs EPICS modules from there

        Args:
            install_path (str): path to parent directory of EPICS
            modules_file (str): path to modules.yml file
        """
        self.log_ = logging.getLogger(__name__)
        self.log_.setLevel(level=logging.DEBUG)
        self.install_path = install_path
        self.support = f"{install_path}/EPICS/support"

        if not os.path.isdir(f"{install_path}/EPICS"):
            os.mkdir(f"{install_path}/EPICS")

        if not os.path.isdir(f"{install_path}/EPICS/support"):
            os.mkdir(f"{install_path}/EPICS/support")

        with open(modules_file, 'r') as file:
            self.module_list = yaml.safe_load(file)

        self.create_dependency_files()

    def create_dependency_files(self):
        """
        Creates RELEASE.local and CONFIG_PARSE.local

        Loops over the modules_list and creates the file lines in two lists then writes the files.
        """

        release_lines = []
        config_lines = []

        for name, module in self.module_list.items():

            # in the case where we use git clone versions aren't added
            # this only happens with seq
            if 'version' in module:
                release_lines.append(f"{module['name']}=$(SUPPORT)/{name}-{module['version']}\n")
            else:
                release_lines.append(f"{module['name']}=$(SUPPORT)/{name}\n")
            # Don't miss additional lines specified
            if 'add_to_file' in module:
                if 'RELEASE' in module['add_to_file']:
                    for item in module['add_to_file']['RELEASE']:
                        release_lines.append(item + '\n')
                if 'CONFIG_SITE' in module['add_to_file']:
                    for item in module['add_to_file']['CONFIG_SITE']:
                        config_lines.append(item + '\n')

        with open(f"{self.support}/RELEASE.local", 'w+') as release_file:
            release_file.writelines(release_lines)

        with open(f"{self.support}/CONFIG_SITE.local", 'w+') as config_file:
            config_file.writelines(config_lines)

    async def get_module(self, name: str,  module: dict):
        """
        Downloads the module

        Args:
            name (str): nickname from yaml file
            module (dict): dictionary of module data
        """

        if "binary" in module:
            if os.path.isdir(f"{self.support}/{name}-{module['version']}"):
                # file already exists
                return

            url = module['binary']
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                file = tarfile.open(fileobj=response.raw, mode="r|gz")
                file.extractall(f"{self.support}")
                return

        elif "git" in module:
            # we don't check git because git clone will ignore it
            process = subprocess.Popen(['git', 'clone', module['git'], name],
                                       cwd=f"{self.support}",
                                       stdout=PIPE, stderr=PIPE)
            stdoutput, stderroutput = process.communicate()
            if 'fatal' not in str(stderroutput) or 'fatal' not in str(stdoutput):
                return

        module.pop(name)
        self.log_.warning(f"Module {name} download failed, skipping install")

    async def install_module(self, name: str,  module: dict):
        """
        Runs make for each file

        Args:
            name (str): nickname from yaml file
            module (dict): dictionary of module data
        """

        if 'version' in module:
            process = subprocess.Popen(['make'],
                                       cwd=f"{self.support}/{name}-{module['version']}",
                                       stdout=PIPE, stderr=PIPE)
        else:
            process = subprocess.Popen(['make'],
                                       cwd=f"{self.support}/{name}",
                                       stdout=PIPE, stderr=PIPE)

        stdoutput, stderroutput = process.communicate()
        if 'Error 2' in str(stderroutput):
            self.log_.error(f"during make: {name} encountered error")
            self.log_.error(f"stderroutput = {str(stderroutput)}")
        else:
            self.log_.info(f"Successfully ran make for {name}")

    async def setup_modules(self):
        """
        Loop over the module list and install each one
        """
        for name, module in self.module_list.items():
            await self.get_module(name, module)

        # separate the download and install to avoid missing dependencies

        for name, module in self.module_list.items():
            await self.install_module(name, module)


async def main():

    if (args_count := len(sys.argv)) > 3:
        print(f"Two arguments expected, got {args_count - 1}")
        raise SystemExit(2)
    elif args_count < 2:
        print("You must specify the target directory")
        raise SystemExit(2)

    install_dir = sys.argv[1]
    modules_file = sys.argv[2]

    if not os.path.isdir(install_dir):
        print("The target directory doesn't exist")
        raise SystemExit(1)

    if not os.path.isfile(modules_file):
        print("Path to modules.yml file doesn't exist")
        raise SystemExit(1)

    print(modules_file)

    installer = EPICS_module_installer("/home/gsc/Github/epics_docker_setup/junk",
                                       "/home/gsc/Github/epics_docker_setup/modules.yml")
    await installer.setup_modules()

if __name__ == "__main__":

    # i don't remember exactly what this does
    PIPE = subprocess.PIPE
    # General log levels are set to WARNING, particular logger will later be changed.
    logging.basicConfig(level=logging.WARNING)

    asyncio.run(main())
