"""Test setup for isotoma.recipe.apache.
"""

import os, re, glob
import pkg_resources

import zc.buildout.testing

import unittest, difflib
import doctest

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('isotoma.recipe.apache', test)
    zc.buildout.testing.install('Jinja2', test)
    zc.buildout.testing.install('missingbits', test)


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
    d = os.path.join(os.path.dirname(__file__))
    testglob = os.path.join(d, "doctests", "*.txt")

    suites = []
    for test in glob.glob(testglob):
        test = os.path.relpath(test, d)
        suites.append(doctest.DocFileSuite(test,
            setUp=setUp, tearDown=zc.buildout.testing.buildoutTearDown,
            optionflags=doctest.ELLIPSIS + doctest.NORMALIZE_WHITESPACE, checker=OutputChecker()))

    return unittest.TestSuite(suites)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
