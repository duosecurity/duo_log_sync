from os import path
from setuptools import setup, find_packages
from duologsync import __version__


HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


with open(path.join(HERE, "requirements.txt"), encoding="utf-8") as f:
    requires = [l.strip() for l in f.readlines()]


with open(path.join(HERE, "requirements-dev.txt"), encoding="utf-8") as f:
    requires_dev = [l.strip() for l in f.readlines()]


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
    install_requires=requires,
    tests_require=requires_dev,
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
