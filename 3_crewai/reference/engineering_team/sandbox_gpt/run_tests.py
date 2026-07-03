import sys
import unittest

suite = unittest.defaultTestLoader.loadTestsFromName('test_backend')
result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
print(f'Ran {result.testsRun} tests')
print(f'Failures: {len(result.failures)}')
print(f'Errors: {len(result.errors)}')
if not result.wasSuccessful():
    sys.exit(1)
