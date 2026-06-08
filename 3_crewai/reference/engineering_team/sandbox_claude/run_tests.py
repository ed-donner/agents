import sys
import unittest

suite = unittest.defaultTestLoader.loadTestsFromName('test_backend')
result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
print(f"tests_run={result.testsRun}")
print(f"failures={len(result.failures)}")
print(f"errors={len(result.errors)}")
print(f"success={result.wasSuccessful()}")
if not result.wasSuccessful():
    raise SystemExit(1)
