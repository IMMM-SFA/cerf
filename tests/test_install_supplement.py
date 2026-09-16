"""Tests for the package data downloader. All HTTP is mocked; no network access is required."""

import io
import os
import tempfile
import unittest
import zipfile
from unittest import mock

import requests

from cerf.install_supplement import InstallSupplement


def make_zip(files):
    """Build an in-memory ZIP archive from a {path: bytes} mapping."""

    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w") as zf:
        for path, data in files.items():
            zf.writestr(path, data)

    return buf.getvalue()


def fake_response(status=200, content=b"", headers=None, url="https://example.test/data.zip", reason="OK"):
    r = mock.Mock(spec=requests.Response)
    r.status_code = status
    r.content = content
    r.headers = headers or {}
    r.url = url
    r.reason = reason

    return r


class TestDownload(unittest.TestCase):

    URL = "https://zenodo.org/records/1/files/cerf_package_data.zip?download=1"
    ZIP = make_zip({"cerf_package_data/a.yml": b"a: 1", "cerf_package_data/sub/b.tif": b"\x00\x01"})

    def setUp(self):
        # no real sleeping during retry tests
        patcher = mock.patch("cerf.install_supplement.time.sleep")
        self.sleep = patcher.start()
        self.addCleanup(patcher.stop)

    def test_success_first_attempt(self):
        with mock.patch("cerf.install_supplement.requests.get", return_value=fake_response(content=self.ZIP)) as get:
            content = InstallSupplement(max_attempts=3).download(self.URL)

        self.assertEqual(content, self.ZIP)
        self.assertEqual(get.call_count, 1)
        self.sleep.assert_not_called()

    def test_rate_limited_then_success_honours_retry_after(self):
        responses = [fake_response(status=429, headers={"Retry-After": "7"}, reason="Too Many Requests"),
                     fake_response(content=self.ZIP)]

        with mock.patch("cerf.install_supplement.requests.get", side_effect=responses) as get:
            content = InstallSupplement(max_attempts=3, backoff_seconds=1).download(self.URL)

        self.assertEqual(content, self.ZIP)
        self.assertEqual(get.call_count, 2)
        self.sleep.assert_called_once_with(7.0)

    def test_transient_5xx_uses_exponential_backoff(self):
        responses = [fake_response(status=503, reason="Service Unavailable"),
                     fake_response(status=502, reason="Bad Gateway"),
                     fake_response(content=self.ZIP)]

        with mock.patch("cerf.install_supplement.requests.get", side_effect=responses):
            InstallSupplement(max_attempts=5, backoff_seconds=2).download(self.URL)

        self.assertEqual([c.args[0] for c in self.sleep.call_args_list], [2, 4])

    def test_connection_error_is_retried(self):
        side_effects = [requests.ConnectionError("reset"), requests.Timeout("slow"), fake_response(content=self.ZIP)]

        with mock.patch("cerf.install_supplement.requests.get", side_effect=side_effects) as get:
            InstallSupplement(max_attempts=3, backoff_seconds=1).download(self.URL)

        self.assertEqual(get.call_count, 3)

    def test_exhausted_retries_raises_with_last_error(self):
        with mock.patch("cerf.install_supplement.requests.get",
                        return_value=fake_response(status=429, reason="Too Many Requests")):
            with self.assertRaises(RuntimeError) as ctx:
                InstallSupplement(max_attempts=3, backoff_seconds=1).download(self.URL)

        self.assertIn("after 3 attempts", str(ctx.exception))
        self.assertIn("HTTP 429", str(ctx.exception))
        self.assertIn(self.URL, str(ctx.exception))

    def test_non_retryable_status_fails_immediately(self):
        with mock.patch("cerf.install_supplement.requests.get",
                        return_value=fake_response(status=404, reason="Not Found")) as get:
            with self.assertRaises(RuntimeError) as ctx:
                InstallSupplement(max_attempts=5).download(self.URL)

        self.assertEqual(get.call_count, 1)
        self.assertIn("HTTP 404", str(ctx.exception))
        self.sleep.assert_not_called()

    def test_html_body_with_200_is_reported_not_passed_to_zipfile(self):
        """The failure mode seen in CI: a 200 whose body is an HTML page, previously surfacing as BadZipFile."""

        html = b"<!DOCTYPE html><html><body>Rate limit exceeded</body></html>"
        resp = fake_response(content=html, headers={"Content-Type": "text/html; charset=utf-8"},
                             url="https://zenodo.org/records/1/files/cerf_package_data.zip")

        with mock.patch("cerf.install_supplement.requests.get", return_value=resp) as get:
            with self.assertRaises(RuntimeError) as ctx:
                InstallSupplement(max_attempts=5).download(self.URL)

        msg = str(ctx.exception)
        self.assertEqual(get.call_count, 1)
        self.assertIn("Expected a ZIP archive", msg)
        self.assertIn("text/html", msg)
        self.assertIn("Rate limit exceeded", msg)
        self.assertIn(self.URL, msg)

    def test_empty_zip_is_accepted_by_magic_check(self):
        empty = make_zip({})

        with mock.patch("cerf.install_supplement.requests.get", return_value=fake_response(content=empty)):
            self.assertEqual(InstallSupplement().download(self.URL), empty)


class TestExtract(unittest.TestCase):

    def test_flattens_directories_and_skips_dir_entries(self):
        content = make_zip({"cerf_package_data/": b"", "cerf_package_data/a.yml": b"a: 1",
                            "cerf_package_data/nested/b.tif": b"\x00\x01"})

        with tempfile.TemporaryDirectory() as tmp:
            dest = os.path.join(tmp, "data")
            out = InstallSupplement.extract(content, dest)

            self.assertEqual(sorted(os.path.basename(p) for p in out), ["a.yml", "b.tif"])
            self.assertEqual(sorted(os.listdir(dest)), ["a.yml", "b.tif"])

            with open(os.path.join(dest, "a.yml"), "rb") as f:
                self.assertEqual(f.read(), b"a: 1")

    def test_corrupt_archive_raises_runtime_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                InstallSupplement.extract(b"PK\x03\x04garbage", tmp)


class TestVersionLookup(unittest.TestCase):

    def test_known_version(self):
        self.assertTrue(InstallSupplement.get_data_link("2.4.1").startswith("https://zenodo.org/records/6998151/"))

    def test_unknown_version_raises_key_error(self):
        with self.assertRaises(KeyError):
            InstallSupplement.get_data_link("0.0.0-nope")

    def test_urls_use_canonical_records_path(self):
        """Zenodo 301-redirects /record/ to /records/; use the canonical path to avoid the extra round trip."""

        for v, url in InstallSupplement.DATA_VERSION_URLS.items():
            self.assertIn("/records/", url, msg=v)


if __name__ == "__main__":
    unittest.main()
