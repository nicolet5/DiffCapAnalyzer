"""A setuptools-based setup module adapted from the Python Packaging Authority's
sample project.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    # Install this project using:
    # $ pip install chachies
    #
    # It lives on PyPI: https://pypi.org/project/chachies/
    name='chachies',

    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    version='1.0',  # Required

    # This is a one-line description or tagline of what your project does. This
    # corresponds to the "Summary" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#summary
    description='Differential capacity plot visualization and machine learning model for battery chemistry classification',  # Required
    url='https://github.com/tacohen/chachies',
    author='The Charged Chinchillas',
    packages=find_packages(),


    install_requires=[
        'certifi==2018.1.18',
        'chardet==3.0.4',
        'idna==2.6',
        'lmfit==0.9.8',
        'numpy==1.14.2',
        'pandas==0.22.0',
        'PeakUtils==1.1.1',
        'python-dateutil==2.7.0',
        'pytz==2018.3',
        'requests==2.18.4',
        'scikit-learn==0.19.1',
        'scipy==1.0.0',
        'six==1.11.0',
        'sklearn==0.0',
        'urllib3==1.22',
        'xlrd==1.1.0'
        'dash==0.21.0'  # The core dash backend
        'dash-renderer==0.11.3'  # The dash front-end
        'dash-html-components==0.9.0'  # HTML components
        'dash-core-components==0.18.1'  # Supercharged components
        'plotly==2.4.1'
    ]

)
