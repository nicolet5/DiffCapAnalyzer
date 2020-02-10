"""A setuptools-based setup module adapted from the Python Packaging Authority"s
sample project.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
import setuptools

# Get the long description from the README file
with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="DiffCapAnalyzer",
    version="0.0.1", 
    author="Nicole Thompson",
    author_email = "nicole.thompson140@gmail.com",
    description="A package for the quantitative analysis of differential capacity data!",
    long_description = long_description, 
    long_description_content_type ="text/markdown", 
    url="https://github.com/nicolet5/DiffCapAnalyzer",
    packages = setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
