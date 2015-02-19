#!/usr/bin/env python
"""
"""

import setuptools

setuptools.setup(
        name='gist',
        version='0.1.0',
        description='Manage github gists',
        license='MIT',
        long_description=(__doc__),
        author='Joshua Downer',
        author_email='joshua.downer@gmail.com',
        url='http://github.com/jdowner/gist',
        keywords='gist github git',
        packages=['gist'],
        package_data={
          '': ['*.rst', 'LICENSE'],
        },
        data_files=[
          ('share/gist/', ['README.rst', 'LICENSE', 'share/gist.bash']),
        ],
        scripts=['bin/gist'],
        platforms=['Unix'],
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'Intended Audience :: End Users/Desktop',
            'Intended Audience :: System Administrators',
            'License :: OSI Approved :: MIT License',
            'Operating System :: Unix',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.0',
            'Programming Language :: Python :: 3.1',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Topic :: Software Development',
            'Topic :: Software Development :: Version Control',
            'Topic :: Utilities',
            ]
        )
