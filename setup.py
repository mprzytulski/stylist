#!/usr/bin/env python

from setuptools import setup, find_packages
import os
import pip

install_reqs = pip.req.parse_requirements(os.path.join(os.path.dirname(__file__), 'requirements.txt'),
                                          session=pip.download.PipSession())
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='stylist',
    version='0.2',
    description='One tool to rule them all',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'stylist=stylist.cli:cli'
        ]
    },
    install_requires=reqs,
    python_requires='>=2.7'
)
