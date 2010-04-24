from setuptools import setup, find_packages

version = '0.0.11'

setup(
    name = 'isotoma.recipe.apache',
    version = version,
    description = "Buildout recipes for apache.",
    url = "http://pypi.python.org/pypi/isotoma.recipe.apache",
    long_description = open("README.rst").read() + "\n" + \
                       open("CHANGES.txt").read(),
    classifiers = [
        "Framework :: Buildout",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX",
        "License :: OSI Approved :: Apache Software License",

    ],
    keywords = "proxy buildout apache",
    author = "Doug Winter",
    author_email = "doug.winter@isotoma.com",
    license="Apache Software License",
    packages = find_packages(exclude=['ez_setup']),
    package_data = {
        '': ['README.rst', 'CHANGES.txt'],
        'isotoma.recipe.apache': ['apache.cfg', 'apache-ssl.cfg']
    },
    namespace_packages = ['isotoma', 'isotoma.recipe'],
    include_package_data = True,
    zip_safe = False,
    install_requires = [
        'setuptools',
        'zc.buildout',
        'Cheetah',
        'isotoma.recipe.gocaptain',
    ],
    entry_points = {
        "zc.buildout": [
            "default = isotoma.recipe.apache:Apache",
        ],
    }
)
