import argparse
import os
import requests
import zipfile

from pkg_resources import get_distribution
from io import BytesIO


class InstallSupplement:
    """Download and unpack example data supplement from Zenodo that matches the current installed
    distribution.

    :param example_data_directory:              Full path to the directory you wish to install
                                                the example data to.  Must be write-enabled
                                                for the user.
    """

    # URL for DOI minted example data hosted on Zenodo
    DATA_VERSION_URLS = {'1.0.0': 'https://doi.org/10.5281/zenodo.3629645'}

    def __init__(self, example_data_directory):

        # full path to the root directory where the example dir will be stored
        self.example_data_directory = example_data_directory

        self.fetch_zenodo()

    def fetch_zenodo(self, model_name='cerf'):
        """Download and unpack the Zenodo example data supplement for the
        current distribution."""

        # get the current version that is installed
        current_version = get_distribution(model_name).version


        try:
            data_link = InstallSupplement.DATA_VERSION_URLS[current_version]

        except KeyError:
            msg = "Link to data missing for current version:  {}.  Please contact admin."
            raise(msg.format(current_version))

        # retrieve content from URL
        print("Downloading supplemental data for version {}".format(current_version))
        r = requests.get(data_link)

        with zipfile.ZipFile(BytesIO(r.content)) as zipped:

            # extract each file in the zipped dir to the project
            for f in zipped.namelist():
                print("Unzipped: {}".format(os.path.join(self.example_data_directory, f)))
                zipped.extract(f, self.example_data_directory)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    help_msg = 'Full path to the directory you wish to install the supplemental data to.'
    parser.add_argument('example_data_directory', type=str, help=help_msg)
    args = parser.parse_args()

    zen = InstallSupplement(args.example_data_directory)
    del zen
