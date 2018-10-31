#!/usr/bin/env python
from __future__ import unicode_literals

try:
    from setuptools import setup, find_packages, Extension
except ImportError:
    from distutils.core import setup

long_description = (
    'Baidusub is forked from autosub from https://github.com/agermanidis/autosub'
    'Baidusub is a utility for automatic speech recognition and subtitle generation. '
    'It takes a video or an audio file as input, performs voice activity detection '
    'to find speech regions, makes parallel requests to Baidu Web Speech API to '
    'generate transcriptions for those regions (will not translates them to a '
    'different language for now) , and finally saves the resulting subtitles to disk. '
    'It can currently produce subtitles in either the SRT format or simple JSON.'
)

setup(
    name='baidusub',
    version='0.1',
    description='Auto-generates subtitles for any video or audio file',
    long_description=long_description,
    author='paaboo',
    author_email='paaboo@live.com',
    url='https://github.com/paaboo/baidusub',
    packages=['baidusub'],
    entry_points={
        'console_scripts': [
            'baidusub = baidusub:main',
        ],
    },
    install_requires=[
        'requests>=2.3.0',
        'pysrt>=1.0.1',
        'progressbar2>=3.34.3',
        'six>=1.11.0',
        'baidu-aip>=2.2.7.0',
    ],
    license=open("LICENSE").read(),
)
