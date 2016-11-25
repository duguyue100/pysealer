"""Setup script for the PySealer package.

Author: Yuhuang Hu
Email : duguyue100@gmail.com
"""

from setuptools import setup

classifiers = """
Development Status :: 3 - Alpha
Intended Audience :: Education
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Topic :: Utilities
Topic :: Scientific/Engineering
Topic :: Software Development :: Pre-processors
License :: OSI Approved :: MIT License
"""

try:
    from pysealer import __about__
    about = __about__.__dict__
except ImportError:
    about = dict()
    exec(open("pysealer/__about__.py").read(), about)

setup(
    name='pysealer',
    version=about["__version__"],

    author=about["__author__"],
    author_email=about["__author_email__"],

    url=about["__url__"],
    #  download_url=about["__download_url__"],

    packages=["pysealer"],
    #  package_data={"": ["/*.*"]},
    #  scripts=["script/"],

    classifiers=list(filter(None, classifiers.split('\n'))),
    description="Yet another standalone Python application creator."
)
