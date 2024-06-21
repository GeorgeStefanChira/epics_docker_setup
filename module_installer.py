####################################################################################################
#
# @file module_installer.py
# @author George S. Chira (gsc@observatorysciences.co.uk)
# @date 21/06/24
# @brief A small python script that instals EPICS modules on Ubuntu 22.04
#
# Takes two arguments:
#
# path to install directory
# path to modules.yml file
#
# The paths to the install directory and modules file can be relative.
#
# If you provide only one argument it will consider it to be the install directory and the modules
# file will be taken from the current working directory.
#
# If no arguments are provided, then the current directory will be considered for both
#
####################################################################################################


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

    folder-name-of-the-module:
        name: "This is the string used in RELEASE files as a path variable"
        version: "Version string as it appears in the link"
        binary: "link to download the binary"
        git: "link to git repo" (this is only used when binary link doesn't exist)
        dependency: "other EPICS modules this depends on"
            - folder-name of dependency 1
            - folder-name of dependency 2
            - folder-name of dependency 3
        add_to_file:
            CONFIG_SITE:
                - "Line to be added to CONFIG_SITE.local"
            RELEASE:
                - "Line to be added to RELEASE.local"

    ----------------

    The modules don't need to be listed in any specific order, as long as you list the dependencies

    Folder-name is used in folder names and when specifying other modules as dependencies.

    The name must always be the string used in the RELEASE files (i.e. ASYN for async).

    Version is required for binary installs but will be ignored when using git cloning. This is
    added to the folder-name when creating folders and creating the RELEASE file.

    Only CONFIG_SITE and RELEASE are parsed when adding extra lines to files.
    """
    ################################################################################################

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

        # Make sure the install paths exist
        if not os.path.isdir(f"{install_path}/EPICS"):
            os.mkdir(f"{install_path}/EPICS")

        if not os.path.isdir(f"{install_path}/EPICS/support"):
            os.mkdir(f"{install_path}/EPICS/support")

        self.support = f"{install_path}/EPICS/support"

        # read the modules file
        with open(modules_file, 'r') as file:
            self.module_dict = yaml.safe_load(file)

        # create RELEASE.local file
        self.create_dependency_files()

        # order the modules so we don't have conflicts when installing them
        self.loop_tracker = []
        self.modules_ordered = []
        for name, module in self.module_dict.items():
            self.check_dependencies(name, module)

        ############################################################################################

    def create_dependency_files(self):
        """
        Creates RELEASE.local and CONFIG_PARSE.local

        Loops over the modules_list and creates the file lines in two lists then writes the files.
        """

        release_lines = []
        config_lines = []

        for name, module in self.module_dict.items():

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

    def check_dependencies(self, name: str, module: dict, previous: str = None):
        """
        Recursive function that sorts install order for the modules

        It starts by following the modules in the order they are listed in the modules file (this
        happens in the init function)

        If the module is already in the ordered list, the function exits, the loop moves on.

        The name is checked for the loop tracker list. This is a list of all the modules that are
        part of the current recursion loop but haven't been installed yet. If the current module
        is there, then a recursion loop is detected between the current module and the previous one
        If it's not in the loop_tracker, then it's added to it. It will be removed at the end.

        If it has one or more dependencies, then the code calls the check_dependencies function on
        each one of it's dependencies. **This is where the recursion process happens**

        Once all the dependencies are sorted, the current module is removed from the loop tracker
        and added to the ordered list.

        This makes sure that all the dependencies of a module are sorted first.

        Suppose the modules file is of the form:

        mod_A:
            dependencies:
                -mod_B
        mod_C:
            dependencies:
                -mod_B
        mod_B:
        mod_D:
            dependencies:
                -mod_E
        mod_E:
            dependencies:
                -mod_D
        mod_F:
            dependencies:
                -mod_C
                -mod_A
                -mod_D
                -mod_B

        The the code will loop over the list [A, C, B, D, E, F]

        When it reaches A, it will recurse into B, install B and then install A.
        For C it will skip B as this is already done.
        B will be skipped
        D will recurse to E, E will try to recurse to D but this will be detected and skipped.
        E will be skipped
        F will recurse into C, skip C, recurse A, skip A and so on

        The install order will then be: [B, A, C, E, D, F]

        This ensures that as long as all the dependencies are referenced once, the correct order
        is always found. Recursions might lead to issues, but the user will be notified
        """
        if name in self.modules_ordered:
            # exit if it's already ordered
            # this happens when multiple modules depend on the same one, or when it appears later
            # in the list than the module that depends on it.
            return

        if name in self.loop_tracker:
            self.log_.error(f"There is a dependency loop between {name} and {previous} module")
            return

        self.loop_tracker.append(name)

        if "dependencies" in module:
            for dependency in module['dependencies']:
                self.check_dependencies(dependency, self.module_dict[dependency], previous=name)

        self.loop_tracker.pop()
        self.modules_ordered.append(name)

        ############################################################################################

    async def get_module(self, name: str,  module: dict):
        """
        Downloads the module

        Args:
            name (str): nickname from yaml file
            module (dict): dictionary of module data
        """

        if "binary" in module:
            if os.path.isdir(f"{self.support}/{name}-{module['version']}"):
                # file already exists -> exit
                return

            url = module['binary']
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                file = tarfile.open(fileobj=response.raw, mode="r|gz")
                file.extractall(f"{self.support}")
                return

        elif "git" in module:
            # we don't check if file exist because git clone will ignore it
            process = subprocess.Popen(['git', 'clone', module['git'], name],
                                       cwd=f"{self.support}",
                                       stdout=PIPE, stderr=PIPE)
            stdoutput, stderroutput = process.communicate()
            if 'fatal' not in str(stderroutput) or 'fatal' not in str(stdoutput):
                return

        module.pop(name)
        self.log_.warning(f"Module {name} download failed, skipping install")

        ############################################################################################

    async def install_module(self, name: str,  module: dict):
        """
        Runs make for each file

        Args:
            name (str): nickname from yaml file
            module (dict): dictionary of module data
        """

        # I could have just used empty version strings, but no, I had to put conditionals everywhere
        if 'version' in module:
            process = subprocess.Popen(['make'],
                                       cwd=f"{self.support}/{name}-{module['version']}",
                                       stdout=PIPE, stderr=PIPE)
        else:
            process = subprocess.Popen(['make'],
                                       cwd=f"{self.support}/{name}",
                                       stdout=PIPE, stderr=PIPE)

        # Some error handling.
        stdoutput, stderroutput = process.communicate()
        if 'Error 2' in str(stderroutput):
            self.log_.error(f"during make: {name} encountered error")
            self.log_.error(f"stderroutput = {str(stderroutput)}")
        else:
            self.log_.info(f"Successfully ran make for {name}")

        ############################################################################################

    async def setup_modules(self):
        """
        Loop over the module list and install each one
        """
        for name in self.modules_ordered:
            module = self.module_dict[name]
            await self.get_module(name, module)

        # separate the download and install to avoid missing dependencies

        for name in self.modules_ordered:
            module = self.module_dict[name]
            await self.install_module(name, module)

        ############################################################################################


def check_path_to_modules(modules_file, current_directory):
    if os.path.isfile(modules_file):
        return modules_file
    if os.path.isfile(f"{modules_file}/modules.yml"):
        return f"{modules_file}/modules.yml"
    if os.path.isfile(f"{current_directory}/{modules_file}"):
        return f"{current_directory}/{modules_file}"
    if os.path.isfile(f"{current_directory}/{modules_file}/modules.yml"):
        return f"{current_directory}/{modules_file}/modules.yml"

    raise FileExistsError("Path to modules.yml file isn't valid")


async def main():
    current_directory = os.path.abspath(os.getcwd())

    # check arguments, autocomplete missing ones
    if (args_count := len(sys.argv)) > 3:
        print(f"Two arguments expected, got {args_count - 1}")
        raise SystemExit(2)
    elif args_count == 3:
        install_dir = sys.argv[1]
        modules_file = sys.argv[2]
    elif args_count == 2:
        install_dir = sys.argv[1]
        modules_file = f"{current_directory}/modules.yml"
    elif args_count == 1:
        install_dir = current_directory
        modules_file = f"{current_directory}/modules.yml"

    if not os.path.isdir(install_dir):
        if os.path.isdir(f"{current_directory}/{install_dir}"):
            install_dir = f"{current_directory}/{install_dir}"
        else:
            raise IsADirectoryError("The target directory doesn't exist")

    modules_file = check_path_to_modules(modules_file, current_directory)

    installer = EPICS_module_installer(install_dir, modules_file)

    await installer.setup_modules()

if __name__ == "__main__":

    # because we use popen asynchronously
    PIPE = subprocess.PIPE

    # General log levels are set to WARNING, particular logger will later be changed.
    logging.basicConfig(level=logging.WARNING)

    asyncio.run(main())
