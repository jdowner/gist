#!/usr/bin/env python

import io
import setuptools
import unittest

def discover_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover("tests", pattern="test_*.py")
    return test_suite


setuptools.setup(
        name='python-gist',
        version='0.6.1',
        description='Manage github gists',
        license='MIT',
        long_description=(io.open('README.rst', 'r', encoding='utf8').read()),
        author='Joshua Downer',
        author_email='joshua.downer@gmail.com',
        url='http://github.com/jdowner/gist',
        keywords='gist github git',
        packages=['gist'],
        package_data={
          '': ['share/*', '*.rst', 'LICENSE'],
        },
        data_files=[
          ('share/gist/', [
              'README.rst',
              'LICENSE',
              'share/gist.bash',
              'share/gist.zsh',
              'share/gist-fzsl.bash',
              'share/gist-fzf.bash',
              ]),
        ],
        scripts=['bin/gist'],
        install_requires=[
            'docopt',
            'python-gnupg>=0.4.1',
            'requests',
            'simplejson',
            ],
        extras_require={
            "dev": [
                "responses",
                "pycodestyle",
                ]
            },
        tests_require = [
            'pycodestyle',
            'responses',
            'tox',
        ],
        platforms=['Unix'],
        test_suite="setup.discover_test_suite",
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: MIT License',
            'Operating System :: Unix',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Software Development',
            'Topic :: Software Development :: Version Control',
            'Topic :: Utilities',
            ]
        )
