from setuptools import setup


def get_requirements():
    """Return a list of package requirements from the requirements.txt file."""
    with open('requirements.txt') as f:
        return f.read().split()


setup(
    install_requires=get_requirements()
)
