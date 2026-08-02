import sys
print('start')
import unittest
print('loaded unittest')
import test_backend
print('loaded test_backend')
suite=unittest.defaultTestLoader.loadTestsFromModule(test_backend)
print('suite count', suite.countTestCases())
runner=unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
print('before run')
result=runner.run(suite)
print('after run', result.wasSuccessful(), result.testsRun, len(result.failures), len(result.errors))
