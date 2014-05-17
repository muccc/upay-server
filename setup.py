import sys
import subprocess

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='nupay',
    version='1.0.0',
    description='Rewrite of upay',
    author='Tobias Schneider',
    author_email='schneider@xtort.eu',
    url='https://github.com/schneider42/nupay',
    packages=['nupay'],
    scripts=['scripts/token-authority-server', 'scripts/mqtt-git-forwarder', 'scripts/mqtt-mail-forwarder'],
    long_description=open('README.md').read(),
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or ",
        "later (GPLv3+)",
        "Programming Language :: Python :: 2",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='nupay upay',
    license='GPLv3+',
)
