#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='upay-server',
    version='1.0.0',
    description='upay token authority server',
    author='Bernd Stolle, Tobias Schneider',
    author_email='bsx+ccc@0xcafec0.de, schneider@xtort.eu',
    url='https://github.com/muccc/upay-server',
    packages=['upay.server'],
    namespace_packages = ['upay'],
    long_description=open('README.md').read(),
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or ",
        "later (GPLv3+)",
        "Programming Language :: Python :: 2",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    requires=["Flask", "sqlalchemy", "jsonschema", "iso8601"],
    entry_points = """
    [console_scripts]
    token-authority-server = upay.server:app.run
    """,
    keywords='upay',
    license='GPLv3+',
)
