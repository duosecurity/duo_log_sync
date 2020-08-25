from os import path
from setuptools import setup, find_packages
from duologsync import __version__

HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name=__version__.__title__,
    version=__version__.__version__,
    description=__version__.__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=__version__.__author__,
    author_email=__version__.__email__,
    url=__version__.__url__,
    license=__version__.__license__,
    packages=find_packages(exclude=['tests']),
    python_requires=">=3.6.2",
    install_requires=["duo_client==4.2.3", "PyYAML==5.3.1", "Cerberus==1.3.2", "six==1.15.0"],
    entry_points={
        "console_scripts": ["duologsync = duologsync.app:main"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: Implementation :: CPython"
    ],
)
