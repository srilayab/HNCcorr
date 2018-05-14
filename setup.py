from setuptools import setup
from setuptools import find_packages
import unittest


def readme():
    with open('README.md') as f:
        return f.read()


def license():
    with open('LICENSE.md') as f:
        return f.read()


setup(name='HNCcorr',
      version='0.1dev',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
      ],
      description=None,
      keywords=['Cell detection', 'Neuroscience', 'Calcium imaging'],
      url='https://github.com/quic0/HNCcorr-python',
      author='Quico Spaen',
      author_email='qspaen@berkeley.edu',
      license=license(),
      long_description=readme(),
      packages=find_packages('src'),
      package_dir={'': 'src'},
      install_requires=['numpy', 'pillow'],  # required packages here
      setup_requires=['pytest-runner', ],
      tests_require=['pytest', 'mock'],
      zip_safe=False
      )
