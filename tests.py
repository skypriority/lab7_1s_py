import io
import unittest
from unittest.mock import patch

import requests

from currencies import get_currencies
from decorators import logger


class FakeResponse:


    def __init__(self, data, error=None):

        self.data = data
        self.error = error

    def raise_for_status(self):

        if self.error:
            raise self.error

    def json(self):

        if self.data is None:
            raise ValueError("bad json")
        return self.data


DATA = {"Valute": {"USD": {"Value": 93.25}, "BAD": {"Value": "x"}}}


class TestGetCurrencies(unittest.TestCase):


    @patch("currencies.requests.get")
    def test_success(self, mock_get):

        mock_get.return_value = FakeResponse(DATA)
        self.assertEqual(get_currencies(["USD"]), {"USD": 93.25})

    @patch("currencies.requests.get")
    def test_missing_currency(self, mock_get):

        mock_get.return_value = FakeResponse(DATA)
        with self.assertRaises(KeyError):
            get_currencies(["EUR"])

    @patch("currencies.requests.get")
    def test_bad_json(self, mock_get):

        mock_get.return_value = FakeResponse(None)
        with self.assertRaises(ValueError):
            get_currencies(["USD"])

    @patch("currencies.requests.get")
    def test_bad_type(self, mock_get):

        mock_get.return_value = FakeResponse(DATA)
        with self.assertRaises(TypeError):
            get_currencies(["BAD"])

    @patch("currencies.requests.get")
    def test_connection_error(self, mock_get):

        mock_get.side_effect = requests.exceptions.ConnectionError()
        with self.assertRaises(ConnectionError):
            get_currencies(["USD"])


class TestLogger(unittest.TestCase):


    def setUp(self):

        self.stream = io.StringIO()

        @logger(handle=self.stream)
        def ok(x):
            return x * 2

        @logger(handle=self.stream)
        def bad():
            raise ValueError("boom")

        self.ok = ok
        self.bad = bad

    def test_success_logging(self):

        self.assertEqual(self.ok(2), 4)
        logs = self.stream.getvalue()
        self.assertIn("INFO", logs)
        self.assertIn("4", logs)

    def test_error_logging(self):

        with self.assertRaises(ValueError):
            self.bad()
        logs = self.stream.getvalue()
        self.assertRegex(logs, "ERROR")
        self.assertIn("ValueError", logs)


class TestStreamWrite(unittest.TestCase):


    def setUp(self):

        self.stream = io.StringIO()

        @logger(handle=self.stream)
        def wrapped():
            return get_currencies(["USD"], url="https://invalid.invalid")

        self.wrapped = wrapped

    def test_logging_error(self):

        with self.assertRaises(ConnectionError):
            self.wrapped()
        logs = self.stream.getvalue()
        self.assertIn("ERROR", logs)
        self.assertIn("ConnectionError", logs)


if __name__ == "__main__":
    unittest.main(verbosity=2)