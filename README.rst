==================================================
GIST
==================================================

'gist' is a command line interface for working with github gists. It provides
several methods for inspecting a users gists, and the ability to easily create
them.

(NB: this is not the package of the same name in available from pip.)


Installation
--------------------------------------------------

To install 'gist' you can either use,
::
  $ sudo python setup.py install

or,
::
  $ sudo make install

This will install the python package 'gist' to the standard location for your
system and copy the license, readme, and bash script into /usr/share/gist. The
bash script contains a function to enable tab-completion. To enable
tab-completion, add
::
  source /usr/share/gist/gist.bash

in your .bashrc file.


Getting started
--------------------------------------------------

'gist' requires a personal access token for authentication. To create a token,
go to https://github.com/settings/applications and generate a new token. The
token needs to then be added to a .gist file in your home directory. The .gist
file should take the form,
::
  [gist]
  token: <enter token here>


Usage
--------------------------------------------------

'gist' is intended to make it easy to manage and use github gists from the
command line. There are several commands available::

  gist create  - creates a new gist
  gist edit    - edit the files in your gist
  gist list    - prints a list of your gists
  gist clone   - clones a gist
  gist delete  - deletes a gist from github
  gist files   - prints a list of the files in a gist
  gist archive - downloads a gist and creates a tarball
  gist content - prints the content of the gist to stdout
  gist info    - prints detailed information about a gist


**gist create**

Most of the 'gist' commands are pretty simple and limited in what they can do.
'gist create' is a little different and offers more flexibility in how the user
can create the gist.

If you have a set of existing files that you want to turn into a gist,
::
  $ gist create "divide et impera" foo.txt bar.txt

where the quoted string is the description of the gist. Or, you may find it
useful to create a gist from content on your clipboard (say, using xclip),
::
  $ xclip -o | gist create "ipsa scientia potestas est"

Another option is to pipe the input into 'gist create' and have it automatically
put the content on github,
::
  $ echo $(cat) | gist create "credo quia absurdum est"

Finally, you can just call,
::
  $ gist create "a posse ad esse"

which will launch your default editor (defined by the EDITOR environment
variable).


**gist edit**

You can edit your gists directly with the 'edit' command. This command will
clone the gist to a temporary directory and open up the default editor (defined
by the EDITOR environment variable) to edit the files in the gist. When the
editor is exited the user is prompted to commit the changes, which are then
pushed back to the remote.


**gist list**

Returns a list of your gists. The gists are returned as,
::
  2b1823252e8433ef8682 - mathematical divagations
  a485ee9ddf6828d697be - notes on defenestration
  589071c7a02b1823252e + abecedarian pericombobulations

The first column is the gists unique identifier; The second column indicates
whether the gist is public ('+') or private ('-'); The third column is the
description in the gist, which may be empty.


**gist clone**

Clones a gist to the current directory. This command will clone any gist based
on its unique identifier (i.e. not just the users) to the current directory.


**gist delete**

Deletes the specified gist.


**gist files**

Returns a list of the files in the specified gist.


**gist archive**

Downloads the specified gist to a temporary directory and adds it to a tarball,
which is then moved to the current directory.


**gist content**

Writes the content of each file in the specified gist to the terminal, e.g.
::
  $ gist content c971fca7997aed65ddc9
  foo.txt:
  this is foo


  bar.txt:
  this is bar


For each file in the gist the first line is the name of the file followed by a
colon, and then the content of that file is written to the terminal.


**gist info**

This command provides a complete dump of the information about the gist as a
JSON object. It is mostly useful for debugging.



Dependencies
--------------------------------------------------

'gist' currently depends on,

* requests
* docopts
