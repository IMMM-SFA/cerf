from setuptools import setup, find_packages



def get_requirements():
    with open('requirements.txt') as f:
        return f.read().split()


setup(
    name='cerf',
    version='2.0.0',
    packages=find_packages(),
    url='https://github.com/IMMM-SFA/cerf',
    license='BSD 2-Clause',
    author='Chris R. Vernon; Nino Zuljevic',
    author_email='chris.vernon@pnnl.gov; nino.zuljevic@pnnl.gov',
    description='A Geospatial Model for Assessing Future Energy Technology Expansion Feasibility',
    install_requires=get_requirements(),
    python_requires='>=3.6',
    include_package_data=True
)
