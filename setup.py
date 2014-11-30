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
    namespace_packages=['upay'],
    long_description=open('README.md').read(),
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or ",
        "later (GPLv3+)",
        "Programming Language :: Python :: 2",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=['Flask', 'sqlalchemy', 'jsonschema', 'iso8601', 'psycopg2'],
    extras_require={
        'tests': ['mock']
    },
    entry_points=dict(
        console_scripts=[
            'token-authority-server = upay.server:app.run',
            'token-authority-bootstrap-db = upay.server.cli:bootstrap_db',
            'token-authority-create-tokens = upay.server.cli:create_tokens',
        ],
    ),
    keywords='upay',
    license='GPLv3+',
)
