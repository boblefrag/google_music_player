import os
from setuptools import setup


def read_relative_file(filename):
    """Returns contents of the given file, which path is supposed relative
    to this module."""
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read().strip()


README = read_relative_file('README.rst')

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


setup(
    name='googlemusicplayer',
    version='0.5',
    packages=['music_player'],
    include_package_data=True,
    description='a GTK music player using google music API',
    long_description=README,
    author='Yohann Gabory',
    author_email="yohann@gabory.fr",
    LICENCE = "BSD",
    CLASSIFIERS = [
        'Programming Language :: Python :: 2.7',
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
    ],
    install_requires=[
        'gmusicapi',
        'python-vlc',
        ' pyasn1>=0.1.8'
    ],
    scripts=['bin/run'],
)
