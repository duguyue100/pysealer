"""Init for PySealer.

Author: Yuhuang Hu
Email : duguyue100@gmail.com
"""

import os
from os.path import join

HOME_PATH = os.environ["HOME"]
PACKAGE_PATH = os.path.dirname(os.path.abspath(__file__))
PYSEALER_PATH = join(HOME_PATH, ".pysealer")
PYSEALER_RES_PATH = join(PYSEALER_PATH, "res")

# create necessary structures for pysealer package

if not os.path.isdir(PYSEALER_PATH):
    os.makedirs(PYSEALER_PATH)

if not os.path.isdir(PYSEALER_RES_PATH):
    os.makedirs(PYSEALER_RES_PATH)
