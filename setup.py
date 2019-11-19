#!/usr/bin/env python
import os
from setuptools import setup

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
README = open(os.path.join(ROOT_DIR, 'README.md')).read()
VERSION = open(os.path.join(ROOT_DIR, 'version.txt')).read()

setup(
    name='django-secrets-manager',
    version=VERSION,
    description='Django SecretsManager is custom secret managers for Django',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Lee HanYeong',
    author_email='dev@lhy.kr',
    license='MIT',
    packages=[
        'django_secrets',
    ],
    install_requires=[
        'boto3',
        'django',
    ],
    url='https://github.com/LeeHanYeong/django-secrets-manager',
    zip_safe=True,
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python',
    ]
)
