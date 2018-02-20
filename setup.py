import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    sys.stdout.write('Missing Package:  setuptools not found.  Demeter requires this to install.  Please install setuptools and retry.')
    sys.exit(1)


def readme():
    with open('README.md') as f:
        return f.read()


def get_requirements():
    with open('requirements.txt') as f:
        return f.read().split()


setup(
    name='cerf',
    version='1.0.0',
    packages=find_packages(),
    url='https://github.com/IMMM-SFA/cerf',
    license='BSD 2-Clause',
    author='Chris R. Vernon; Nino Zuljevic',
    author_email='chris.vernon@pnnl.gov; nino.zuljevic@pnnl.gov',
    description='A Geospatial Model for Assessing Future Energy Technology Expansion Feasibility',
    long_description=readme(),
    install_requires=get_requirements()
)
