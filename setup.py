#!/usr/bin/env python
import ast
import codecs
import os
import re
from setuptools import find_packages, setup

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))
init = os.path.join(ROOT, 'src', 'admin_sync', '__init__.py')

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open(init, 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

def read(*parts):
    here = os.path.abspath(os.path.dirname(__file__))
    return codecs.open(os.path.join(here, *parts), "r").read()

requirements = ["django-admin-extra-buttons>=1.5.1", "requests"]
constance_require = ["django-picklefield", "django-constance"]
tests_require = [
    "black",
    "django-concurrency",
    "django-reversion",
    "django-smart-admin",
    "django-webtest",
    "factory-boy",
    "flake8<5",
    "flake8-html",
    "freezegun",
    "isort",
    "pytest",
    "pytest-coverage",
    "pytest-django",
    "pytest-echo",
    "pytest-responses",
    "redis",
    "tox",
]
dev_require = [
    "django",
    "pdbpp",
]
docs_require = read('docs/requirements.txt')

setup(
    name='django-admin-sync',
    version=version,
    url='https://github.com/saxix/django-admin-sync',
    download_url='https://github.com/saxix/django-admin-sync',
    author='sax',
    author_email='s.apostolico@gmail.com',
    description="",
    license='MIT',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    install_requires=requirements,
    tests_require=tests_require,
    extras_require={
        'test': tests_require + constance_require,
        'dev': dev_require + tests_require,
        'docs': docs_require,
        'constance': constance_require,
    },
    zip_safe=False,
    platforms=['any'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Operating System :: OS Independent',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Intended Audience :: Developers'],
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)
