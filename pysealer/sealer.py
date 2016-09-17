"""The app sealer.

Author: Yuhuang Hu
Email : duguyue100@gmail.com
"""

from __future__ import print_function
import os
from os.path import isdir, join
import shutil

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
        """Configure environment based on a .pysealer_config file."""

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
            if isdir(f_path):
                shutil.copytree(f_path, join(self.build_src, f_name),
                                ignore=shutil.ignore_patterns('*.py'))
