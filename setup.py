# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 16:20:21 2019

@author: iskander.shafikov
"""

from setuptools import setup

setup(
    name='yxml',
    version='0.1',
    packages=[''],
    install_requires=[
        'requests>=2.21.0', 'fire>=0.1.3'
    ],
    entry_points='''
        [console_scripts]
        yxml=yxml:main
    ''',
)