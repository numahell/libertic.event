"""
Launching all doctests in the tests directory using:

    - the base layer in testing.py

"""
# GLOBALS avalaible in doctests
# IMPORT/DEFINE objects there or inside ./user_globals.py (better)
# globals from the testing product are also available.
# example:
# from for import bar
# and in your doctests, you can do:
# >>> bar.something
from libertic.event.tests.globals import *
from libertic.event.testing import (
    LIBERTIC_EVENT_FUNCTIONAL_TESTING as FUNCTIONAL_TESTING,
    LIBERTIC_EVENT_SIMPLE as SIMPLE,
    LIBERTIC_EVENT_MOCK as MOCK,
    LIBERTIC_EVENT_INTEGRATION_TESTING as INT,
)


import unittest2 as unittest
import glob
import os
import logging
import doctest
from plone.testing import layered

optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)

def test_suite():
    """."""
    logger = logging.getLogger('libertic.event.tests')
    cwd = os.path.dirname(__file__)
    files = []
    try:
        files = []
        for e in ['*rst', '*txt']:
            for d in [cwd, 
                      os.path.dirname(cwd)]:
                files += glob.glob(os.path.join(d, e))
    except Exception,e:
        logger.warn('No doctests for libertic.event')
    suite = unittest.TestSuite()
    globs = globals()
    for s in files:
        layer = FUNCTIONAL_TESTING
        if s.split(os.path.sep)[-1].startswith('simple_'):
            layer = SIMPLE
        if s.split(os.path.sep)[-1].startswith('mock_'):
            layer = MOCK 
        if s.split(os.path.sep)[-1].startswith('int_'):
            layer = INT 
        suite.addTests([
            layered(
                doctest.DocFileSuite(
                    s, 
                    globs = globs,
                    module_relative=False,
                    optionflags=optionflags,         
                ),
                layer=layer
            ),
        ])
    return suite
    
# vim:set ft=python:
