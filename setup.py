import re
from setuptools import setup, find_packages


def readme():
    """Return the contents of the project README file."""
    with open('README.md') as f:
        return f.read()


def get_requirements():
    """Return a list of package requirements from the requirements.txt file."""
    with open('requirements.txt') as f:
        return f.read().split()


version = re.search(r"__version__ = ['\"]([^'\"]*)['\"]", open('cerf/__init__.py').read(), re.M).group(1)


setup(
    name='cerf',
    version="2.0.0",
    packages=find_packages(),
    url='https://github.com/IMMM-SFA/cerf',
    license='BSD2-Simplified',
    author='Chris R. Vernon; Nino Zuljevic',
    author_email='chris.vernon@pnnl.gov; nino.zuljevic@pnnl.gov',
    description='An open-source geospatial Python package for assessing and analyzing future electricity technology capacity expansion feasibility',
    long_description=readme(),
    long_description_content_type="text/markdown",
    python_requires='>=3.7.*, <4',
    include_package_data=True,
    install_requires=get_requirements()
)
