==================================================
GIST
==================================================

'gist' is a command line interface for working with github gists. It provides
several methods for inspecting a users gists, and the ability to easily create
them.


Installation
--------------------------------------------------

To install 'gist' you can either use,::

  $ sudo python setup.py install

or,::

  $ sudo make install

This will install the python package 'gist' to the standard location for your
system and copy the license, readme, and bash script into /usr/share/gist. The
bash script contains a function to enable tab-completion. To enable
tab-completion, add::

  source /usr/share/gist/gist.bash

in your .bashrc file.


Getting started
--------------------------------------------------

'gist' requires a personal access token for authentication. To create a token,
go to https://github.com/settings/applications and generate a new token. The
token needs to then be added to a .gist file in your home directory. The .gist
file should take the form,::

  [gist]
  token: <enter token here>


Usage
--------------------------------------------------

'gist' is intended to make it easy to manage and use github gists from the
command line. There are several commands available:::

  gist list    - prints a list of your gists
  gist info    - prints detailed information about a gist
  gist files   - prints a list of the files in a gist
  gist delete  - deletes a gist from github
  gist archive - downloads a gist and creates a tarball
  gist content - prints the content of the gist to stdout
  gist create  - creates a new gist
  gist clone   - clones a gist

The commands do exactly what they state, but 'gist create' is a little more
interesting than the rest. It is possible to use it to create a gist from a set
of files,::

  $ git create "divide et impera" foo.txt bar.txt

but often it is useful to take create a gist from data that may be on the
clipboard,::

  $ xclip -o | gist create "ipsa scientia potestas est"

or, perhaps, you want to create some quick notes and put them in a gist,::

  $ echo $(cat) | gist create "credo quia absurdum est"


Dependencies
--------------------------------------------------

'gist' currently depends on,

* requests
* docopts
