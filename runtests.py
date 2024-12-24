#!/usr/bin/env python

import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


def main():
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(failfast=True)
    # kept here to run a single test
    failures = test_runner.run_tests(
        [
            "tests.test_index.IndexTestCase"
        ]
    )
    # failures = test_runner.run_tests(["tests"])
    sys.exit(bool(failures))


if __name__ == "__main__":
    main()
