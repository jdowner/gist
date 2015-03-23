#!/usr/bin/env python

import setuptools

def dependencies():
    packages = ['tox']
    with open("requirements.txt") as fp:
        packages.extend(line for line in fp.readlines() if line)

    return packages


setuptools.setup(
        name='python-gist',
        version='0.2.1',
        description='Manage github gists',
        license='MIT',
        long_description=(open('README.rst').read()),
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
              'share/gist-fzsl.bash',
              'share/gist-fzf.bash',
              ]),
        ],
        scripts=['bin/gist'],
        install_requires=dependencies(),
        platforms=['Unix'],
        test_suite="tests",
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
            'Topic :: Software Development',
            'Topic :: Software Development :: Version Control',
            'Topic :: Utilities',
            ]
        )
