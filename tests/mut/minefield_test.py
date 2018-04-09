"""
minefield_test.py - Test the minefield module

April 2018, Lewis Gaul
"""

import sys
from os.path import basename, splitext
import logging
import unittest

from minegauler.minefield import *
from ..utils import mut_dir


def create_minefield_test():
    logging.info("Initialising minefield")
    mf = Minefield(5, 7)
    logging.debug("%r\n%s", mf, mf)
    logging.info("Filling minefield with list of coords")
    mf.create_from_list([(0, 2), (2, 6), (3, 4), (2, 0),
                         (0, 3), (1, 5), (2, 3), (3, 2)])
    logging.debug("%r\n%s", mf, mf)
    logging.debug("Minefield has 3bv of %d", mf.bbbv)
    logging.debug("Completed board is:\n%s", mf.completed_board)
    
    logging.info("Initialising minefield with multiple mines per cell")
    mf = Minefield(4, 1)
    logging.debug("%r\n%s", mf, mf)
    logging.info("Filling minefield with list of coords")
    mf.create_from_list([(2, 0), (1, 0), (1, 0), (1, 0), (0, 0)], per_cell=10)
    logging.debug("%r\n%s", mf, mf)
    logging.debug("Minefield has 3bv of %d", mf.bbbv)
    logging.debug("Completed board is:\n%s", mf.completed_board)
    

tests = [create_minefield_test]


def run(create=False):
    fname = splitext(basename(__file__))[0] + '.log'
    baseline_path = join(mut_dir, 'logs', fname)
    temp_path = join(mut_dir, 'logs', 'temp_' + fname)
    if create:
        fpath = baseline_path
    else:
        fpath = temp_path
    logging.basicConfig(filename=fpath, filemode='w', level=logging.DEBUG)
    # Run all tests.
    for test in tests:
        test()
    # If not in create mode, check that the output matches the baseline log.
    if not create:
        with open(baseline_path, 'r') as base_file, \
             open(temp_path, 'r') as temp_file:
            if base_file.read() != temp_file.read():
                print("Files don't match, test FAILED")
            else:
                print("Files match, test PASSED")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '-c':
        print("Overwriting log")
        run(create=True)
    else:
        run()