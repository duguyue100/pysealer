"""Utilities for PySealer.

Author: Yuhuang Hu
Email : duguyue100@gmail.com
"""

from __future__ import print_function
from os.path import isdir


def get_conda(target_path, platform="osx", pyver=2, arch=64):
    """Get lastest miniconda by given platform.

    Parameters
    ----------
    target_path : string
        The miniconda save path, raise IO error if it's not a valid folder.
    platform : string
        "osx", "linux", or "windows"
    pyver : int
        Python 2 : 2
        Python 3 : 3
    arch : int
        32bit : 32
        64bit : 64

    Returns
    -------
    A miniconda copy and saved to target path
    """
    if not isdir(target_path):
        raise IOError("The target path %s is not existed!" % (target_path))

    down_url = "https://repo.continuum.io/miniconda/"

    # specify version
    down_url = down_url+"Miniconda2-latest-" \
        if pyver == 2 else down_url+"Miniconda3-latest-"

    # specify platform
    if platform == "osx":
        down_url += "MacOSX-"
    elif platform == "linux":
        down_url += "Linux-"
    elif platform == "windows":
        down_url += "Windows-"

    # specify architecture
    if platform != "osx":
        down_url = down_url+"x86.sh" if arch == 32 else down_url+"x86_64.sh"
    else:
        down_url += "x86_64.sh"

    print ("[MESSAGE] Downloading Miniconda from %s..." % (down_url))
