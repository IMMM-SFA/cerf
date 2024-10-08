import os
import tempfile
import zipfile
import shutil

import requests

from pkg_resources import get_distribution
from io import BytesIO as BytesIO

import cerf.package_data as pkg


class InstallSupplement:
    """Download and unpack example data supplement from Zenodo that matches the current installed
    cerf distribution.

    :param data_dir:                    Optional.  Full path to the directory you wish to store the data in.  Default is
                                        to install it in data directory of the package.

    :type data_dir:                     str

    """

    # URL for DOI minted example data hosted on Zenodo
    DATA_VERSION_URLS = {
        '2.0.0': 'https://zenodo.org/record/5218436/files/cerf_package_data.zip?download=1',
        '2.0.1': 'https://zenodo.org/record/5218436/files/cerf_package_data.zip?download=1',
        '2.0.2': 'https://zenodo.org/record/5218436/files/cerf_package_data.zip?download=1',
        '2.0.3': 'https://zenodo.org/record/5218436/files/cerf_package_data.zip?download=1',
        '2.0.4': 'https://zenodo.org/record/5247690/files/cerf_package_data.zip?download=1',
        '2.0.5': 'https://zenodo.org/record/5247690/files/cerf_package_data.zip?download=1',
        '2.0.6': 'https://zenodo.org/record/5247690/files/cerf_package_data.zip?download=1',
        '2.0.7': 'https://zenodo.org/record/5514010/files/cerf_package_data.zip?download=1',
        '2.0.8': 'https://zenodo.org/record/5514010/files/cerf_package_data.zip?download=1',
        '2.0.9': 'https://zenodo.org/record/5514010/files/cerf_package_data.zip?download=1',
        '2.1.0': 'https://zenodo.org/record/5514010/files/cerf_package_data.zip?download=1',
        '2.1.1': 'https://zenodo.org/record/5514010/files/cerf_package_data.zip?download=1',
        '2.2.0': 'https://zenodo.org/record/6998151/files/cerf_package_data.zip?download=1',
        '2.2.1': 'https://zenodo.org/record/6998151/files/cerf_package_data.zip?download=1',
        '2.3': 'https://zenodo.org/record/6998151/files/cerf_package_data.zip?download=1',
        '2.3.1': 'https://zenodo.org/record/6998151/files/cerf_package_data.zip?download=1',
        '2.3.2': 'https://zenodo.org/record/6998151/files/cerf_package_data.zip?download=1',
        '2.3.3': 'https://zenodo.org/record/6998151/files/cerf_package_data.zip?download=1',
        '2.4.0': 'https://zenodo.org/record/6998151/files/cerf_package_data.zip?download=1',
    }

    def __init__(self, data_dir=None):

        self.data_dir = data_dir

    def fetch_zenodo(self):
        """Download and unpack the Zenodo example data supplement for the
        current cerf distribution."""

        # full path to the cerf root directory where the example dir will be stored
        if self.data_dir is None:
            data_directory = pkg.get_data_directory()
        else:
            data_directory = self.data_dir

        # get the current version of cerf that is installed
        current_version = get_distribution('cerf').version

        try:
            data_link = InstallSupplement.DATA_VERSION_URLS[current_version]

        except KeyError:
            msg = f"Link to data missing for current version:  {current_version}.  Please contact admin."

            raise KeyError(msg)

        # retrieve content from URL
        print("Downloading example data for cerf version {}...".format(current_version))
        r = requests.get(data_link)

        with zipfile.ZipFile(BytesIO(r.content)) as zipped:

            # extract each file in the zipped dir to the project
            for f in zipped.namelist():

                extension = os.path.splitext(f)[-1]

                if len(extension) > 0:

                    basename = os.path.basename(f)
                    out_file = os.path.join(data_directory, basename)

                    # extract to a temporary directory to be able to only keep the file out of the dir structure
                    with tempfile.TemporaryDirectory() as tdir:

                        # extract file to temporary directory
                        zipped.extract(f, tdir)

                        # construct temporary file full path with name
                        tfile = os.path.join(tdir, f)

                        print(f"Unzipped: {out_file}")
                        # transfer only the file sans the parent directory to the data package
                        shutil.copy(tfile, out_file)


def install_package_data(data_dir=None):
    """Download and unpack example data supplement from Zenodo that matches the current installed
    cerf distribution.

    :param data_dir:                    Optional.  Full path to the directory you wish to store the data in.  Default is
                                        to install it in data directory of the package.

    :type data_dir:                     str

    """

    zen = InstallSupplement(data_dir=data_dir)

    zen.fetch_zenodo()
