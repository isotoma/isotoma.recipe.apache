"""Test setup for isotoma.recipe.apache.
"""

import os, re
import pkg_resources

import zc.buildout.testing

import unittest
import zope.testing
from zope.testing import doctest, renormalizing


def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('isotoma.recipe.apache', test)
    zc.buildout.testing.install('isotoma.recipe.gocaptain', test)
    zc.buildout.testing.install('zope.testing', test)
    zc.buildout.testing.install('Cheetah', test)
    zc.buildout.testing.install('Markdown', test)
    zc.buildout.testing.install('Jinja2', test)


checker = renormalizing.RENormalizing([
    #zc.buildout.testing.normalize_path,
    (re.compile('#![^\n]+\n'), ''),
    (re.compile('-\S+-py\d[.]\d(-\S+)?.egg'),
     '-pyN.N.egg',
    ),
    ])


def test_suite():
    tests = [
        "doctests/apache.txt",
        "doctests/apache-rewrites.txt",
        "doctests/apache-wsgi.txt",
        "doctests/apache-redirect.txt",
        "doctests/apache-redirect-additional-params.txt",
        "doctests/includes.txt",
        "doctests/apache-ldap.txt",
        "doctests/apache-ssl.txt",
        ]

    suites = []
    for test in tests:
        suites.append(doctest.DocFileSuite(test,
            setUp=setUp, tearDown=zc.buildout.testing.buildoutTearDown,
            optionflags=doctest.ELLIPSIS, checker=checker))

    return unittest.TestSuite(suites)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
