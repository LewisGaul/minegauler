"""
run_all_tests.py - Run all the MUTs

April 2018, Lewis Gaul
"""

from os.path import join, abspath, dirname
from importlib import import_module


# As new tests are created they should be added to this list.
test_names = ['minefield_test']
# Import the tests so that they can be run.
tests = []
for test in test_names:
    tests.append(import_module('tests.mut.' + test, 'minegauler'))


def main():
    for test in tests:
        test.run()
        

if __name__ == '__main__':
    main()