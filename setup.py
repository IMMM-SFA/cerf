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
    version=version,
    packages=find_packages(),
    url='https://github.com/IMMM-SFA/cerf',
    download_url=f'https://github.com/IMMM-SFA/cerf/archive/refs/tags/v{version}.tar.gz',
    license='BSD-2-Clause',
    author='Chris R. Vernon; Nino Zuljevic',
    author_email='chris.vernon@pnnl.gov',
    description='An open-source geospatial Python package for assessing and analyzing future electricity technology capacity expansion feasibility',
    long_description=readme(),
    long_description_content_type="text/markdown",
    python_requires='>=3.7.*, <4',
    include_package_data=True,
    install_requires=[
        'numpy>=1.19.4',
        'pandas>=1.1.4',
        'rasterio>=1.2.3',
        'xarray>=0.16.1',
        'PyYAML>=5.4.1',
        'requests>=2.25.1',
        'joblib>=1.0.1',
        'matplotlib>=3.3.3',
        'seaborn>=0.11.1',
        'whitebox>=1.5.1',
        'fiona>=1.8.19',
        'pyproj>=3.0.1',
        'rtree>=0.9.7',
        'shapely>=1.7.1',
        'geopandas>=0.9.0'
    ],
    extras_require={
        'dev': [
            'build>=0.5.1',
            'nbsphinx>=0.8.6',
            'setuptools>=57.0.0',
            'sphinx>=4.0.2',
            'sphinx-panels>=0.6.0',
            'sphinx-rtd-theme>=0.5.2',
            'twine>=3.4.1',
            'pytest>=6.2.4',
            'pytest-cov>=2.12.1'
        ]
    }
)
