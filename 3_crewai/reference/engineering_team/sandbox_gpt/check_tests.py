import sys
import unittest

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromName('test_backend')
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    print('SUCCESS' if result.wasSuccessful() else 'FAILURE')
    raise SystemExit(0 if result.wasSuccessful() else 1)
