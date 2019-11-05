#!/usr/bin/env python

import io
import os
import setuptools


setuptools.setup(
    name="python-gist",
    version="0.9.0",
    description="Manage github gists",
    license="MIT",
    long_description=(io.open("README.rst", "r", encoding="utf8").read()),
    author="Joshua Downer",
    author_email="joshua.downer@gmail.com",
    url="http://github.com/jdowner/gist",
    keywords="gist github git",
    packages=["gist"],
    package_data={"": [os.sep.join(["share", "*"]), "*.rst", "LICENSE"]},
    data_files=[
        (
            os.sep.join(["share", "gist"]),
            [
                "README.rst",
                "LICENSE",
                os.sep.join(["share", "gist.bash"]),
                os.sep.join(["share", "gist.zsh"]),
                os.sep.join(["share", "gist-fzsl.bash"]),
                os.sep.join(["share", "gist-fzf.bash"]),
            ],
        )
    ],
    install_requires=["docopt", "python-gnupg>=0.4.1", "requests", "simplejson"],
    platforms=["Unix", "Windows"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development",
        "Topic :: Software Development :: Version Control",
        "Topic :: Utilities",
    ],
    # `scripts` provides a non portable approach to creating binaries on the target
    # `entry_points` is the recommended way to let setuptools do all the hard work.
    entry_points={"console_scripts": ["gist = gist.client:main"]},
)
