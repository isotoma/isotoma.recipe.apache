"""Test setup for isotoma.recipe.apache.
"""

import os, re
import pkg_resources

import zc.buildout.testing

import unittest, difflib
import doctest

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('isotoma.recipe.apache', test)
    zc.buildout.testing.install('Jinja2', test)


class OutputChecker(doctest.OutputChecker):

    regexp = re.compile('<BLANKLINE>\n')

    def transform(self, inp):
        inp = self.regexp.sub('', inp)
        lines = [x.strip() for x in inp.split('\n') if x.strip()]
        return lines

    def check_output(self, want, got, optionflags):
        want = '\n'.join(self.transform(want))
        got = '\n'.join(self.transform(got))

        return doctest.OutputChecker.check_output(self, want, got, optionflags)

    def output_difference(self, example, got, optionflags):
        want = self.transform(example.want)
        got = self.transform(got)

        return '\n'.join(difflib.unified_diff(want, got, "want", "got"))


def test_suite():
    tests = [
        "doctests/apache.txt",
        "doctests/apache-rewrites.txt",
        "doctests/apache-request-header.txt",
        "doctests/apache-header.txt",
        "doctests/apache-wsgi.txt",
        "doctests/apache-wsgi-ssl.txt",
        "doctests/apache-wsgi-auth.txt",
        "doctests/apache-wsgi-protected.txt",
        "doctests/apache-redirect.txt",
        "doctests/apache-redirect-ssl.txt",
        "doctests/apache-redirect-additional-params.txt",
        "doctests/includes.txt",
        "doctests/apache-ldap.txt",
        "doctests/apache-ssl.txt",
        "doctests/apache-maintenance.txt",
        ]

    suites = []
    for test in tests:
        suites.append(doctest.DocFileSuite(test,
            setUp=setUp, tearDown=zc.buildout.testing.buildoutTearDown,
            optionflags=doctest.ELLIPSIS + doctest.NORMALIZE_WHITESPACE, checker=OutputChecker()))

    return unittest.TestSuite(suites)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
