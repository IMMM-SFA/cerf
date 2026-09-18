import logging
import os
import shutil
import tempfile
import time
import zipfile
from importlib.metadata import version
from io import BytesIO as BytesIO

import requests

import cerf.package_data as pkg

logger = logging.getLogger(__name__)


# ZIP archives begin with the local file header signature "PK\x03\x04"; an empty archive begins with "PK\x05\x06"
ZIP_MAGIC_PREFIXES = (b"PK\x03\x04", b"PK\x05\x06")


class InstallSupplement:
    """Download and unpack example data supplement from Zenodo that matches the current installed
    cerf distribution.

    :param data_dir:                    Optional.  Full path to the directory you wish to store the data in.  Default is
                                        to install it in data directory of the package.
    :type data_dir:                     str

    :param max_attempts:                Number of download attempts before giving up. Zenodo enforces rate limits
                                        (HTTP 429) and occasionally returns transient 5xx errors, both of which are
                                        retried with exponential backoff. Default 5.
    :type max_attempts:                 int

    :param timeout:                     Per-request timeout in seconds. Default 300.
    :type timeout:                      float

    :param backoff_seconds:             Initial backoff between attempts in seconds; doubles each retry. A
                                        ``Retry-After`` header from the server takes precedence when present.
                                        Default 5.
    :type backoff_seconds:              float

    """

    # URL for DOI minted example data hosted on Zenodo
    DATA_VERSION_URLS = {
        '2.0.0': 'https://zenodo.org/records/5218436/files/cerf_package_data.zip?download=1',
        '2.0.1': 'https://zenodo.org/records/5218436/files/cerf_package_data.zip?download=1',
        '2.0.2': 'https://zenodo.org/records/5218436/files/cerf_package_data.zip?download=1',
        '2.0.3': 'https://zenodo.org/records/5218436/files/cerf_package_data.zip?download=1',
        '2.0.4': 'https://zenodo.org/records/5247690/files/cerf_package_data.zip?download=1',
        '2.0.5': 'https://zenodo.org/records/5247690/files/cerf_package_data.zip?download=1',
        '2.0.6': 'https://zenodo.org/records/5247690/files/cerf_package_data.zip?download=1',
        '2.0.7': 'https://zenodo.org/records/5514010/files/cerf_package_data.zip?download=1',
        '2.0.8': 'https://zenodo.org/records/5514010/files/cerf_package_data.zip?download=1',
        '2.0.9': 'https://zenodo.org/records/5514010/files/cerf_package_data.zip?download=1',
        '2.1.0': 'https://zenodo.org/records/5514010/files/cerf_package_data.zip?download=1',
        '2.1.1': 'https://zenodo.org/records/5514010/files/cerf_package_data.zip?download=1',
        '2.2.0': 'https://zenodo.org/records/6998151/files/cerf_package_data.zip?download=1',
        '2.2.1': 'https://zenodo.org/records/6998151/files/cerf_package_data.zip?download=1',
        '2.3': 'https://zenodo.org/records/6998151/files/cerf_package_data.zip?download=1',
        '2.3.1': 'https://zenodo.org/records/6998151/files/cerf_package_data.zip?download=1',
        '2.3.2': 'https://zenodo.org/records/6998151/files/cerf_package_data.zip?download=1',
        '2.3.3': 'https://zenodo.org/records/6998151/files/cerf_package_data.zip?download=1',
        '2.4.0': 'https://zenodo.org/records/6998151/files/cerf_package_data.zip?download=1',
        '2.4.1': 'https://zenodo.org/records/6998151/files/cerf_package_data.zip?download=1',
        '2.5.0': 'https://zenodo.org/records/6998151/files/cerf_package_data.zip?download=1',
    }

    # HTTP status codes worth retrying: rate limited, and transient server-side failures
    RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)

    def __init__(self, data_dir=None, max_attempts=5, timeout=300, backoff_seconds=5):

        self.data_dir = data_dir
        self.max_attempts = max_attempts
        self.timeout = timeout
        self.backoff_seconds = backoff_seconds

    @staticmethod
    def _version_key(version_string):
        """Sortable tuple for a release version string such as ``'2.3'`` or ``'2.4.1'``.

        Any local / dev suffix (``'2.5.0.dev3'``, ``'2.5.0+g1234'``, ``'2.5.0rc1'``) is dropped so development
        builds of a release resolve like the release itself. Returns ``None`` when no leading numeric release
        segment can be parsed (e.g., the ``'0.0.0+unknown'`` fallback is parsed as ``(0, 0, 0)``, a genuinely
        malformed string is not).

        """

        parts = []
        for piece in str(version_string).split('.'):
            digits = ''
            for ch in piece:
                if ch.isdigit():
                    digits += ch
                else:
                    break
            if not digits:
                break
            parts.append(int(digits))
            if len(digits) != len(piece):
                break  # stop at the first non-numeric suffix, e.g. '0rc1' or '0+g1234'

        return tuple(parts) if parts else None

    @classmethod
    def get_data_link(cls, current_version):
        """Return the data URL for a cerf version.

        An exact entry in ``DATA_VERSION_URLS`` wins. Otherwise the URL registered for the **newest version not newer
        than** the installed one is used, with a warning, so a patch or minor release that did not change the data
        supplement keeps working without a code change here. Versions older than every registered entry, or
        unparsable versions, raise ``KeyError`` as before.

        :param current_version:         Installed cerf version string
        :type current_version:          str

        :return:                        URL to the versioned data archive

        """

        if current_version in cls.DATA_VERSION_URLS:
            return cls.DATA_VERSION_URLS[current_version]

        wanted = cls._version_key(current_version)

        if wanted is not None:
            candidates = [(cls._version_key(v), v) for v in cls.DATA_VERSION_URLS]
            eligible = [(key, v) for key, v in candidates if key is not None and key <= wanted]

            if eligible:
                _, fallback_version = max(eligible)
                logger.warning(f"No package data registered for cerf version {current_version}; using the data "
                               f"released for version {fallback_version}. If a newer data supplement exists for "
                               f"this release, please update `InstallSupplement.DATA_VERSION_URLS`.")
                return cls.DATA_VERSION_URLS[fallback_version]

        msg = (f"Link to data missing for current version:  {current_version}.  Registered versions: "
               f"{', '.join(cls.DATA_VERSION_URLS)}.  Please contact admin.")

        raise KeyError(msg)

    @staticmethod
    def _retry_delay(response, attempt, backoff_seconds):
        """Seconds to wait before the next attempt, honouring a numeric ``Retry-After`` header when present."""

        retry_after = None if response is None else response.headers.get("Retry-After")

        if retry_after is not None:
            try:
                return max(float(retry_after), 0.0)
            except ValueError:
                pass

        return backoff_seconds * (2 ** attempt)

    def download(self, data_link):
        """Download the archive at ``data_link`` and return its bytes.

        Retries on connection errors, timeouts, and retryable HTTP status codes with exponential backoff.
        Raises ``RuntimeError`` with the URL, final status, content type, and a snippet of the body if the
        server never returns a ZIP archive. This replaces the previous behaviour of handing whatever bytes came
        back straight to ``zipfile``, which surfaced rate-limit HTML pages as an opaque ``BadZipFile``.

        :param data_link:               URL to download
        :type data_link:                str

        :return:                        Archive content as bytes

        """

        last_error = None
        response = None

        for attempt in range(self.max_attempts):

            try:
                response = requests.get(data_link, timeout=self.timeout, allow_redirects=True)

            except (requests.ConnectionError, requests.Timeout) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                response = None

            else:

                if response.status_code == 200:

                    content = response.content

                    if content.startswith(ZIP_MAGIC_PREFIXES):
                        return content

                    # a 200 that is not a ZIP is almost always an HTML error/consent page; do not retry
                    content_type = response.headers.get("Content-Type", "unknown")
                    snippet = content[:200].decode("utf-8", errors="replace")

                    raise RuntimeError(
                        f"Expected a ZIP archive from {data_link} but received {len(content)} bytes of "
                        f"'{content_type}' (final URL: {response.url}). Response begins with: {snippet!r}"
                    )

                last_error = f"HTTP {response.status_code} ({response.reason})"

                if response.status_code not in self.RETRYABLE_STATUS_CODES:
                    raise RuntimeError(
                        f"Failed to download cerf package data from {data_link}: {last_error} "
                        f"(final URL: {response.url})"
                    )

            if attempt < self.max_attempts - 1:
                delay = self._retry_delay(response, attempt, self.backoff_seconds)
                logger.warning(
                    f"Download attempt {attempt + 1}/{self.max_attempts} failed ({last_error}); "
                    f"retrying in {delay:.0f} s"
                )
                time.sleep(delay)

        raise RuntimeError(
            f"Failed to download cerf package data from {data_link} after {self.max_attempts} attempts. "
            f"Last error: {last_error}"
        )

    @staticmethod
    def extract(content, data_directory):
        """Extract every file in the archive into ``data_directory``, flattening any parent directories.

        :param content:                 ZIP archive content
        :type content:                  bytes

        :param data_directory:          Destination directory
        :type data_directory:           str

        :return:                        List of extracted file paths

        """

        os.makedirs(data_directory, exist_ok=True)

        extracted = []

        try:
            archive = zipfile.ZipFile(BytesIO(content))

        except zipfile.BadZipFile as exc:
            raise RuntimeError("Downloaded cerf package data is not a valid ZIP archive") from exc

        with archive as zipped:

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

                    extracted.append(out_file)

        return extracted

    def fetch_zenodo(self):
        """Download and unpack the Zenodo example data supplement for the
        current cerf distribution."""

        # full path to the cerf root directory where the example dir will be stored
        if self.data_dir is None:
            data_directory = pkg.get_data_directory()
        else:
            data_directory = self.data_dir

        # get the current version of cerf that is installed
        current_version = version('cerf')

        data_link = self.get_data_link(current_version)

        # retrieve content from URL
        print(f"Downloading example data for cerf version {current_version} from {data_link} ...")
        content = self.download(data_link)

        return self.extract(content, data_directory)


def install_package_data(data_dir=None, max_attempts=5, timeout=300):
    """Download and unpack example data supplement from Zenodo that matches the current installed
    cerf distribution.

    :param data_dir:                    Optional.  Full path to the directory you wish to store the data in.  Default is
                                        to install it in data directory of the package.
    :type data_dir:                     str

    :param max_attempts:                Number of download attempts before giving up (Zenodo rate limits and
                                        transient errors are retried with exponential backoff). Default 5.
    :type max_attempts:                 int

    :param timeout:                     Per-request timeout in seconds. Default 300.
    :type timeout:                      float

    """

    zen = InstallSupplement(data_dir=data_dir, max_attempts=max_attempts, timeout=timeout)

    zen.fetch_zenodo()
