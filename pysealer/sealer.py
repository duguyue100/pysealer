"""The app sealer.

Author: Yuhuang Hu
Email : duguyue100@gmail.com
"""

from __future__ import print_function
import os
from os.path import isdir, isfile, join
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
                 target_platform="osx", pyver=2, arch=64):
        """Init a Sealer class."""
        if isdir(app_path):
            self.app_path = app_path
        else:
            raise IOError("The App root path %s is not existed!" % (app_path))

        if host_platform in ["osx", "windows", "linux"]:
            self.host_platform = host_platform
        else:
            raise ValueError("The target platform %s is "
                             "not supported." % (host_platform))

        if target_platform in ["osx", "windows", "linux"]:
            self.target_platform = target_platform
        else:
            raise ValueError("The target platform %s is "
                             "not supported." % (target_platform))

        if pyver in [2, 3]:
            self.pyver = pyver
        else:
            raise ValueError("The python version %d "
                             "is not supported" % (pyver))

        if arch in [32, 64]:
            self.arch = arch
        else:
            raise ValueError("The architecture %d is not supported" % (arch))

        # init the right miniconda for the host and target python
        self.host_conda = utils.get_conda(platform=self.host_platform,
                                          pyver=self.pyver,
                                          arch=self.arch)
        print ("[MESSAGE] Host conda environment is downloaded.")

        self.target_conda = utils.get_conda(platform=self.target_platform,
                                            pyver=self.pyver,
                                            arch=self.arch)
        print ("[MESSAGE] Target conda environment is downloaded.")

    def init_build(self):
        """Initialize the app building environment."""
        # install the host python distribution at app build folder.
        self.build_path = join(self.app_path, "pysealer_build")
        if not isdir(self.build_path):
            os.makedirs(self.build_path)

        # prepare for build src folder
        self.build_src = join(self.build_path, "src")
        if not isdir(self.build_src):
            os.makedirs(self.build_src)

        # install miniconda at the path
        self.build_conda = join(self.build_path, "miniconda")
        if not isdir(self.build_conda):
            sp.check_call(["chmod", "+x", self.host_conda])
            sp.check_call([self.host_conda, "-b", "-p",
                           self.build_conda])
        print ("[MESSAGE] The miniconda at %s is "
               "installed at %s" % (self.host_conda, self.build_conda))

        self.build_bin = join(self.build_conda, "bin")

    def config_environment(self):
        """Configure environment based on a .pysealer_config.yml file.

        Setup environment by specifying:
        conda_install
        pip_install
        app_list

        in YAML format.
        """
        self.config_path = join(self.app_path, ".pysealer_config.yml")
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
        print ("[MESSAGE] PIP dependencies are installed.")
        sp.check_call([self.build_conda, "list"])
        shutil.copy2(self.config_path, self.build_path)
        print ("[MESSAGE] Building environment is configured.")

    def compile_app(self):
        """Build entire app and redirect it to build path."""
        # install all dependencies through conda

        # indentify the right python
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
