# setup.py
from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="code_flowchart",
    version="{{VERSION_PLACEHOLDER}}",
    description="A simple tool for creating flowcharts of code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="16st58",
    author_email="kithree1010@gmail.com",
    url="https://github.com/16st58/code-flowchart",
    packages=find_packages(),             # Recognize the folder with __init__.py as a package
    install_requires=[
        "graphviz",
    ],
    entry_points={
        "console_scripts": [
            # Running the ode_flowchart command runs the main function of cli.py
            "code_flowchart=code_flowchart.cli:main"
        ]
    },
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
