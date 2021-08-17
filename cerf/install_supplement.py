import os
import zipfile
import pkg_resources

import requests

from pkg_resources import get_distribution
from io import BytesIO as BytesIO


class InstallSupplement:
    """Download and unpack example data supplement from Zenodo that matches the current installed
    cerf distribution.

    """

    # URL for DOI minted example data hosted on Zenodo
    DATA_VERSION_URLS = {'2.0.0': 'https://zenodo.org/record/3856417/files/test.zip?download=1',
                         '2.0.1': 'https://zenodo.org/record/3856417/files/test.zip?download=1',
                         '2.0.2': 'https://zenodo.org/record/3856417/files/test.zip?download=1',
                         '2.0.3': 'https://zenodo.org/record/3856417/files/test.zip?download=1',
                         '2.0.4': 'https://zenodo.org/record/3856417/files/test.zip?download=1'}

    def fetch_zenodo(self):
        """Download and unpack the Zenodo example data supplement for the
        current cerf distribution."""

        # full path to the cerf root directory where the example dir will be stored
        data_directory = pkg_resources.resource_filename('cerf', 'data')

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
                print("Unzipped: {}".format(os.path.join(data_directory, f)))
                zipped.extract(f, data_directory)


def install_package_data():
    """Download and unpack example data supplement from Zenodo that matches the current installed
    cerf distribution.

    """

    zen = InstallSupplement()

    zen.fetch_zenodo()
