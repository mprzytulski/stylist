#!/usr/bin/env python

from setuptools import setup, find_packages
import os, pip

install_reqs = pip.req.parse_requirements(os.path.join(os.path.dirname(__file__), 'requirements.txt'),
                                          session=pip.download.PipSession())
reqs = [str(ir.req) for ir in install_reqs]

setup(name='stylist',
      version='0.1',
      description='One tool to rule them all',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      entry_points={
          'console_scripts': [
              'stylist=stylist.cli:cli'
          ]
      },
      install_requires=reqs,
      python_requires='>=3.6'
)

