"""The app sealer.

Author: Yuhuang Hu
Email : duguyue100@gmail.com
"""

from __future__ import print_function
import os
from os.path import isdir, isfile, join
import datetime
import shutil
import yaml

from pysealer import utils

try:
    import subprocess32 as sp
except ImportError:
    import subprocess as sp


class Sealer():
    """The central class that wraps a target python application."""

    def __init__(self, app_path, host_platform="osx",
                 target_platform="osx", pyver=2,
                 host_arch=64, target_arch=64):
        """Init a Sealer class."""
        # App's Core Path
        if isdir(app_path):
            self.app_path = app_path
        else:
            raise IOError("The App root path %s is not existed!" % (app_path))

        # Host Platform (where you compile the code)
        if host_platform in ["osx", "windows", "linux"]:
            self.host_platform = host_platform
        else:
            raise ValueError("The target platform %s is "
                             "not supported." % (host_platform))

        # Target Platform (where you deliver the code)
        if target_platform in ["osx", "windows", "linux"]:
            self.target_platform = target_platform
        else:
            raise ValueError("The target platform %s is "
                             "not supported." % (target_platform))

        # The python version of the code
        if pyver in [2, 3]:
            self.pyver = pyver
        else:
            raise ValueError("The python version %d "
                             "is not supported" % (pyver))

        # System architecture
        if host_arch in [32, 64]:
            self.host_arch = host_arch
        else:
            raise ValueError("The architecture %d is not supported"
                             % (host_arch))

        if target_arch in [32, 64]:
            self.target_arch = target_arch
        else:
            raise ValueError("The architecture %d is not supported"
                             % (target_arch))

        # Package configuration path
        self.config_path = join(self.app_path, ".pysealer_config.yml")

        # General path configuration
        self.build_path = join(self.app_path, "pysealer_build")
        self.build_src = join(self.build_path, "src")
        self.build_conda = join(self.build_path, "miniconda")
        self.build_bin = join(self.build_conda, "bin")

        # init the right miniconda for the host and target python
        self.host_downurl, self.host_conda = utils.get_conda(
            platform=self.host_platform, pyver=self.pyver,
            arch=self.host_arch)
        print ("[MESSAGE] Host conda environment is downloaded.")

        self.target_downurl, self.target_conda = utils.get_conda(
            platform=self.target_platform, pyver=self.pyver,
            arch=self.target_arch)
        print ("[MESSAGE] Target conda environment is downloaded.")

    def init_build(self):
        """Initialize the app building environment."""
        # install the host python distribution at app build folder.
        if not isdir(self.build_path):
            os.makedirs(self.build_path)
            print ("[MESSAGE] App local build path is at %s"
                   % (self.build_path))
        else:
            shutil.rmtree(self.build_path)
            os.makedirs(self.build_path)
            print ("[MESSAGE] App local build path is cleaned up!")

        # prepare for build src folder
        if not isdir(self.build_src):
            os.makedirs(self.build_src)

        # install miniconda at the path
        if not isdir(self.build_conda):
            sp.check_call(["chmod", "+x", self.host_conda])
            sp.check_call([self.host_conda, "-b", "-p",
                           self.build_conda])
        print ("[MESSAGE] The miniconda at %s is "
               "installed at %s" % (self.host_conda, self.build_conda))

    def config_environment(self):
        """Configure environment based on a .pysealer_config.yml file.

        Setup environment by specifying:
        conda_install
        pip_install
        app_list

        in YAML format.
        """
        if not isfile(self.config_path):
            print ("[MESSAGE] No valid .pysealer_config.yml is found "
                   "for the project, skip environment configuration.")
            return

        with open(self.config_path, mode="r") as f:
            config_dict = yaml.load(f)

        print ("[MESSAGE] Configuring environment...")
        # install conda item
        self.build_conda = join(self.build_bin, "conda")
        sp.check_call([self.build_conda, "info", "-a"])
        sp.check_call([self.build_conda, "update", "--yes", "conda"])
        sp.check_call([self.build_conda, "install", "--yes", "conda-build"])
        sp.check_call([self.build_conda, "install", "--yes", "pip"])
        for conda_item in config_dict["conda_install"]:
            sp.check_call([self.build_conda, "install", "--yes", conda_item])
        print ("[MESSAGE] Conda dependencies are installed.")

        # install pip items
        self.build_pip = join(self.build_bin, "pip")
        sp.check_call([self.build_pip, "--version"])
        for pip_item in config_dict["pip_install"]:
            if pip_item == "requirements.txt":
                if isfile(join(self.app_path, pip_item)):
                    sp.check_call([self.build_pip, "install", "-r",
                                   join(self.app_path, pip_item)])
            else:
                #  attempt to do the normal install
                #  TODO: There may be duplicated install for certain
                #        package. Right now, it's developer's responsibility
                #        to do this job.
                sp.check_call([self.build_pip, "install", pip_item])

        print ("[MESSAGE] PIP dependencies are installed.")
        sp.check_call([self.build_conda, "list"])
        shutil.copy2(self.config_path, self.build_path)
        print ("[MESSAGE] Building environment is configured.")

    def compile_app(self):
        """Build entire app and redirect it to build path."""
        # install all dependencies through conda

        # identify the right python
        self.build_python = join(self.build_bin, "python")
        sp.check_call([self.build_python, "--version"])

        folder_list = os.listdir(self.app_path)
        folder_list.remove("pysealer_build")

        for f_name in folder_list:
            f_path = join(self.app_path, f_name)
            if isdir(f_path):
                # compile it!
                sp.check_call([self.build_python, "-m", "compileall",
                               f_path])
                print ("[MESSAGE] %s is compiled!" % (f_path))

    def prepare_app(self):
        """Replicate the app structure and copy the file into builder path."""
        folder_list = os.listdir(self.app_path)
        folder_list.remove("pysealer_build")

        for f_name in folder_list:
            f_path = join(self.app_path, f_name)
            if isdir(f_path) and not isdir(join(self.build_src, f_name)):
                shutil.copytree(f_path, join(self.build_src, f_name),
                                ignore=shutil.ignore_patterns('*.py'))

        print ("[MESSAGE] The project is saved to %s" % (self.build_src))

    def seal_app(self):
        """The final procedures for sealing the app.

        1. bash file that set general parameters at client end.
        2. bash file that setup environment at client end.
        3. bash file that compile a list of running bash file for compiling as
           app.
        4. Wrap the entire app as an installer.
        """
        # Start to write a bash file
        self.seal_path = join(self.app_path, "sealed_app")

        if not isdir(self.seal_path):
            os.makedirs(self.seal_path)
            print ("[MESSAGE] The sealed app is stored at %s"
                   % (self.seal_path))
        else:
            # clean up the sealed app directory
            shutil.rmtree(self.seal_path)
            os.makedirs(self.seal_path)
            print ("[MESSAGE] The sealed app path is cleaned up!")

        # copy configuration
        # directly embed all the commands to the shell script, not gonna parse
        # YAML in the shell script.
        if isfile(self.config_path):
            shutil.copy2(self.config_path, self.seal_path)
            print ("[MESSAGE] The app configuration is stored at %s"
                   % (join(self.seal_path, ".pysealer_config.yml")))
            self.seal_config_path = join(self.seal_path,
                                         ".pysealer_config.yml")

            with open(self.seal_config_path, mode="r") as f:
                config_dict = yaml.load(f)
            self.app_name = config_dict["app_name"][0]
            self.app_version = config_dict["app_version"][0]
            self.app_author = config_dict["app_author"][0]
        else:
            print ("[MESSAGE] No valid .pysealer_config.yml is found "
                   "for the project, skip environment configuration.")
            self.app_name = "app"
            self.app_version = "v0.1.0"
            self.app_author = "John Doe"

        # try to copy requirement file
        if isfile(join(self.app_path, "requirements.txt")):
            shutil.copy2(join(self.app_path, "requirements.txt"),
                         self.seal_app)

        # copy compiled source
        self.seal_src_path = join(self.seal_path, "src")
        if not isdir(self.seal_src_path):
            shutil.copytree(self.build_src, self.seal_src_path)
            print ("[MESSAGE] The compiled source is stored at %s"
                   % (self.seal_src_path))

        # construct build script
        self.build_script_path = join(self.seal_path, "build.sh")
        if isfile(self.build_script_path):
            os.remove(self.build_script_path)
            print ("[MESSAGE] Old build script detected, removed.")

        self.build_script_file = open(self.build_script_path, "w")

        # header
        self.build_script_file.write("#!/bin/bash\n\n")
        self.build_script_file.write("# Build script for %s %s by %s\n"
                                     % (self.app_name, self.app_version,
                                        self.app_author))
        self.build_script_file.write("# "+str(datetime.datetime.now())+"\n\n")
        self.build_script_file.flush()

        # general path
        self.build_script_file.write('# General Path Parameters\n\n')
        self.build_script_file.write(
                'echo "[MESSAGE] Set general parameters."\n')
        self.build_script_file.write('APP_PATH=${PWD}\n')
        self.build_script_file.write('export APP_PATH\n')

        self.build_script_file.write('SRC_PATH=${APP_PATH}/src\n')
        self.build_script_file.write('export SRC_PATH\n')

        self.build_script_file.write('MINICONDA_PATH=${APP_PATH}/miniconda\n')
        self.build_script_file.write('export MINICONDA_PATH\n')

        self.build_script_file.write('CONDA_BIN=${MINICONDA_PATH}/bin\n')
        self.build_script_file.write('export CONDA_BIN\n')

        self.build_script_file.write('CONDA=${CONDA_BIN}/conda\n')
        self.build_script_file.write('export CONDA\n')

        self.build_script_file.write('PIP=${CONDA_BIN}/pip\n')
        self.build_script_file.write('export PIP\n')

        self.build_script_file.write('PYTHON=${CONDA_BIN}/python\n')
        self.build_script_file.write('export PYTHON\n\n')

        self.build_script_file.write(
            'echo "[MESSAGE] The app is located at $APP_PATH"\n')
        self.build_script_file.write(
            'echo "[MESSAGE] The compile file is located at $SRC_PATH"\n')
        self.build_script_file.write(
            'echo "[MESSAGE] miniconda is located at $MINICONDA_PATH"\n')
        self.build_script_file.write(
            'echo "[MESSAGE] miniconda binaries are located at $CONDA_BIN"\n')
        self.build_script_file.write(
            'echo "[MESSAGE] conda binary is located at $CONDA"\n')
        self.build_script_file.write(
            'echo "[MESSAGE] pip binary is located at $PIP"\n')
        self.build_script_file.write(
            'echo "[MESSAGE] python binary is located at $PYTHON"\n')

        self.build_script_file.write('\n')
        self.build_script_file.flush()

        # possible option

        # Install Miniconda
        self.build_script_file.write(
            '# Install miniconda in the current folder\n\n')

        self.build_script_file.write(
            '# The target platform is %s\n' % (self.target_platform))
        if self.target_platform == "osx":
            self.build_script_file.write(
                'curl -o miniconda.sh %s\n\n' % (self.target_downurl))
        elif self.target_platform == "linux":
            self.build_script_file.write(
                'wget -O miniconda.sh %s\n\n' % (self.target_downurl))

        self.build_script_file.write(
            'chmod +x ${APP_PATH}/miniconda.sh\n')
        self.build_script_file.write(
            '${APP_PATH}/miniconda.sh -b -p ${MINICONDA_PATH}\n')
        self.build_script_file.write(
            'echo "[MESSAGE] The target miniconda is built."\n')
        self.build_script_file.write(
            'rm ${APP_PATH}/miniconda.sh')

        self.build_script_file.write('\n')
        self.build_script_file.flush()

        # build conda installation
        self.build_script_file.write('# Install Conda Dependencies\n\n')

        self.build_script_file.write('$CONDA info -a\n')
        self.build_script_file.write('$CONDA update --yes conda\n')
        self.build_script_file.write('$CONDA install --yes conda-build\n')
        self.build_script_file.write('$CONDA install --yes pip\n')
        for conda_item in config_dict["conda_install"]:
            self.build_script_file.write(
                '$CONDA install --yes %s\n' % (conda_item))

        self.build_script_file.write('\n')
        self.build_script_file.flush()

        # build pip installation
        self.build_script_file.write('# Install pip Dependencies\n\n')

        self.build_script_file.write('$PIP --version\n')
        for pip_item in config_dict["pip_install"]:
            if pip_item == "requirements.txt":
                if isfile(join(self.seal_path, pip_item)):
                    self.build_script_file.write(
                        '$PIP install -r %s\n'
                        % (join(self.seal_path, pip_item)))
            else:
                #  attempt to do the normal install
                #  TODO: There may be duplicated install for certain
                #        package. Right now, it's developer's responsibility
                #        to do this job.
                self.build_script_file.write(
                        '$PIP install %s\n' % (pip_item))

        # clean conda
        self.build_script_file.write(
            '$CONDA clean --all --yes')
        self.build_script_file.write('\n')
        self.build_script_file.flush()

        self.build_script_file.write(
            '# [MESSAGE] The build script ends here.')
        self.build_script_file.close()
        sp.check_call(["chmod", "+x", self.build_script_path])
        print ("[MESSAGE] The environment build script is prepared at %s"
               % (self.build_script_path))

        # construct optional environment arguments
        opt_env_args = ""
        if "opt_env_args" in config_dict:
            for arg in config_dict["opt_env_args"]:
                opt_env_args += arg+" "

        # Build application list
        for app_item in config_dict['app_list']:
            app_folder_path = join("./src", app_item)
            for app_script in config_dict['app_list'][app_item]:
                if isfile(join(self.seal_path, app_script+".sh")):
                    print ("[MESSAGE] The current app is existed!")
                    continue
                app_script_file = open(
                    join(self.seal_path, app_script+".sh"), "w")

                app_script_file.write("#!/bin/bash\n\n")
                app_script_file.write(
                    "# App script for %s by %s\n"
                    % (app_script, self.app_author))
                app_script_file.write(
                    "# "+str(datetime.datetime.now())+"\n\n")
                app_script_file.flush()

                app_script_file.write(
                    '# General Parameter Settings\n')
                app_script_file.write('APP_PATH=${PWD}\n')
                app_script_file.write('export APP_PATH\n')

                app_script_file.write('SRC_PATH=${APP_PATH}/src\n')
                app_script_file.write('export SRC_PATH\n')

                app_script_file.write('MINICONDA_PATH=${APP_PATH}/miniconda\n')
                app_script_file.write('export MINICONDA_PATH\n')

                app_script_file.write('CONDA_BIN=${MINICONDA_PATH}/bin\n')
                app_script_file.write('export CONDA_BIN\n')

                app_script_file.write('PYTHON=${CONDA_BIN}/python\n')
                app_script_file.write('export PYTHON\n\n')

                app_script_file.write('# Running command\n')
                app_script_file.write(
                    'PYTHONPATH=${SRC_PATH}:$PYTHONPATH %s ${PYTHON} %s "$@"'
                    % (opt_env_args, join(app_folder_path, app_script+".pyc")))

                app_script_file.close()

                sp.check_call(["chmod", "+x",
                               join(self.seal_path, app_script+".sh")])

                print ("[MESSAGE] The app running script is prepared at %s"
                       % (join(self.app_path, app_script+".sh")))

        if not isdir(join(self.app_path, self.app_name)):
            os.rename(join(self.app_path, "sealed_app"),
                      join(self.app_path, self.app_name))
        print ("[MESSAGE] The pre-sealed package is prepared.")

    def makeself(self, makeself=None):
        """Use Makeself for building up installer."""
        if makeself is None:
            # Assume you have a environment value as makeself
            makeself = os.environ["makeself"]

        with open(self.config_path, mode="r") as f:
            config_dict = yaml.load(f)

        app_name = config_dict["app_name"][0]
        app_version = config_dict["app_version"][0]
        app_author = config_dict["app_author"][0]
        sp.check_call([makeself, "--notemp",
                       join(self.app_path, app_name),
                       join(self.app_path, app_name+".run"),
                       app_name+" "+app_version+" by "+app_author,
                       "./build.sh"])
        print ("[MESSAGE] The installer is built.")
