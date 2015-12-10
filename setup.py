import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from distutils.command.build_py import build_py

path, script = os.path.split(sys.argv[0])
os.chdir(os.path.abspath(path))

install_requires = ['asyncio >= 3.4.3', 'aiohttp >= 0.19']

with open('LONG_DESCRIPTION.rst') as f:
    long_description = f.read()

# Don't import aiostripe module here, since deps may not be installed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aiostripe'))
VERSION = __import__('version').VERSION

setup(
    name='aiostripe',
    cmdclass={'build_py': build_py},
    version=VERSION,
    description='Stripe python bindings (with asyncio!)',
    long_description=long_description,
    author='Stripe',
    author_email='support@stripe.com',
    url='https://github.com/stripe/stripe-python',
    packages=['aiostripe', 'aiostripe.test', 'coroutils', 'uniondict'],
    package_data={'aiostripe': ['data/ca-certificates.crt']},
    install_requires=install_requires,
    test_suite='aiostripe.test.all',
    tests_require=[],
    # use_2to3=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ])
