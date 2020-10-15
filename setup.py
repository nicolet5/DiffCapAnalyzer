"""A setuptools-based setup module adapted from the Python Packaging Authority"s
sample project.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

import setuptools

# Get the long description from the README file
with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="DiffCapAnalyzer",
    version="1.0.1",
    author="Nicole Thompson",
    author_email="nicole.thompson140@gmail.com",
    description="A package for the quantitative analysis of differential capacity data!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    download_url="https://github.com/nicolet5/DiffCapAnalyzer/archive/v0.1.1.tar.gz",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "asteval>=0.9.18",
        "atomicwrites>=1.3.0",
        "attrs>=19.3.0",
        "certifi>=2019.11.28",
        "chardet>=3.0.4",
        "Click>=7.0",
        "colorama>=0.4.3",
        "coverage>=5.0.3",
        "cycler>=0.10.0",
        "dash>=1.8.0",
        "dash-core-components>=1.7.0",
        "dash-html-components>=1.0.2",
        "dash-renderer>=1.2.3",
        "dash-table>=4.6.0",
        "dash-table-experiments>=0.6.0",
        "Flask>=1.1.1",
        "Flask-Compress>=1.4.0",
        "future>=0.18.2",
        "idna>=2.8",
        "itsdangerous>=1.1.0",
        "Jinja2>=2.10.3",
        "kiwisolver>=1.1.0",
        "lmfit>=1.0.0",
        "MarkupSafe>=1.1.1",
        "matplotlib>=3.1.2",
        "more-itertools>=8.1.0",
        "numpy>=1.18.1",
        "packaging>=20.1",
        "pandas>=0.25.3",
        "PeakUtils>=1.3.3",
        "plotly>=4.5.0",
        "pluggy>=0.13.1",
        "py>=1.8.1",
        "pyparsing>=2.4.6",
        "pytest>=5.3.4",
        "pytest-cov>=2.8.1",
        "python-dateutil>=2.8.1",
        "pytz>=2019.3",
        "requests>=2.22.0",
        "retrying>=1.3.3",
        "scipy>=1.4.1",
        "six>=1.14.0",
        "ua-parser>=0.8.0",
        "uncertainties>=3.1.2",
        "urllib3>=1.25.8",
        "wcwidth>=0.1.8",
        "Werkzeug>=0.16.0",
        "wincertstore>=0.2"
    ],
    tests_require=[
        'pytest',
        'pytest-cov'
    ]
)
