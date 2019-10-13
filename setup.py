import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="ESPN_Manager",
    version="1.0.0",
    author="Daniel Slocum",
    author_email="",
    description="",
    license="BSD",
    keywords="example documentation tutorial",
    # url="http://packages.python.org/ESPN_Manager",
    packages=['ESPN_Manager', 'requests', 'pandas', 'beautifulsoup4', 'test'],
    long_description=read('README'),
    scripts=[],
    install_requires=['beautifulsoup4', 'pandas', 'requests', 'numpy', 'fuzzywuzzy']
)
