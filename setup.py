"""Setup script for traktor_nowplaying."""
from setuptools import setup, find_packages, Command
from shutil import rmtree
import codecs
import io
import os
import sys

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    """Return multiple read calls to different readable objects as a single string."""
    return codecs.open(os.path.join(here, *parts), 'r').read()

NAME = 'traktor_nowplaying'
DESCRIPTION = f'{NAME} uses Traktor\'s broadcast functionality to extract metadata about the currently playing song.'
LONG_DESCRIPTION = read('README.md')
URL = 'https://github.com/radusuciu/traktor_nowplaying'
EMAIL = 'radusuciu@gmail.com'
AUTHOR = 'Radu Suciu'

# not doing import because do not want to have to load module
# before it has been installed
version_path = os.path.join(here, 'traktor_nowplaying/version.py')
exec(read(version_path))
VERSION = __version__


# from github.com/kennethreitz/setup.py
class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            rmtree(os.path.join(here, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution…')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPi via Twine…')
        os.system('twine upload dist/*')

        sys.exit()


setup(
    name=NAME,
    version=VERSION,
    url=URL,
    author=AUTHOR,
    author_email=EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    packages=find_packages(exclude=('tests',)),
    entry_points={
        'console_scripts': ['traktor_nowplaying=traktor_nowplaying.cli:main']
    },
    include_package_data=True,
    platforms='any',
    zip_safe=True,
    license='MIT License',
    classifiers=[
        'Environment :: Console',
        'Topic :: Multimedia :: Sound/Audio',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
)