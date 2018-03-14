from __future__ import absolute_import, division, print_function
from os.path import join as pjoin

# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
_version_major = 0
_version_minor = 1
_version_micro = ''  # use '' for first of series, number for 1 and above
_version_extra = 'dev'
# _version_extra = ''  # Uncomment this for full releases

# Construct full version string from these.
_ver = [_version_major, _version_minor]
if _version_micro:
    _ver.append(_version_micro)
if _version_extra:
    _ver.append(_version_extra)

__version__ = '.'.join(map(str, _ver))

CLASSIFIERS = ["Development Status :: In Developement",
               "Environment :: Console",
               "Intended Audience :: Researchers",
               "License :: OSI Approved :: MIT License",
               "Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Batteries and Charged Chinchillas"]

# Description should be a one-liner:
description = "Chachies: a program to help understand battery data."
# Long description will go up on the pypi page
long_description = """
Chachies
========
Chachies is a program to visualize and classify the chemistry of
batteries using machine learning and a DASH console.
To get started using these components in your own software, please go to the
repository README_.
.. _README: https://github.com/tacohen125/chachies/blob/master/README.md
License
=======
``chachies`` is licensed under the terms of the MIT license. See the file
"LICENSE" for information on the history of this software, terms & conditions
for usage, and a DISCLAIMER OF ALL WARRANTIES.
All trademarks referenced herein are property of their respective holders.
Copyright (c) 2018--, Nicole Thompson, Sarah Alamdari, Robert Masse,
Theodore Cohen
"""

NAME = "chachies"
MAINTAINER = "Nicole Thompson"
MAINTAINER_EMAIL = "nicolet5@uw.edu"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
URL = "https://github.com/tacohen125/chachies"
DOWNLOAD_URL = ""
LICENSE = "MIT"
AUTHOR = "Nicole Thompson, Sarah Alamdari, Robert Masse, Theodore Cohen"
AUTHOR_EMAIL = "nicolet5@uw.edu"
PLATFORMS = "OS Independent"
MAJOR = _version_major
MINOR = _version_minor
MICRO = _version_micro
VERSION = __version__
PACKAGE_DATA = {'chachies': [pjoin('data', '*')]}
REQUIRES = ["Python3, LMFit, numpy, pandas, peakUtils, scikit-learn," +
			"scipy, sklearn, xlrd, DASH, plotly"]