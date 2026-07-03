"""Inline test runner: imports test_backend and runs unittest in-process."""
import sys
import unittest

import test_backend  # noqa: F401 - import to register tests

loader = unittest.TestLoader()
suite = loader.loadTestsFromModule(test_backend)
runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
result = runner.run(suite)

print("====")
print(f"tests_run={result.testsRun}")
print(f"failures={len(result.failures)}")
print(f"errors={len(result.errors)}")
print(f"success={result.wasSuccessful()}")

for name, tb in list(result.failures) + list(result.errors):
    print("=" * 60)
    print(name)
    print(tb)
