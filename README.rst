==================================================
GIST
==================================================

'gist' is a command line interface for working with github gists. It provides
several methods for inspecting a users gists, and the ability to easily create
them.

.. image:: https://github.com/jdowner/gist/workflows/gist%20continuous%20integration/badge.svg
    :target: https://github.com/jdowner/gist


Requirements
--------------------------------------------------
Python 3.6, 3.7, 3.8, or 3.9 is required.


Installation
--------------------------------------------------

The preferred way to install 'gist' is from pypi.org using pip (or pip3),

::

  $ pip install python-gist

Alternatively, you can clone the repository and install it manually,

::

  $ pip install .

The 'share' directory contains a set of shell scripts that provide tab
completion and fuzzy search for gist. There are 3 different scripts for
tab-completion in bash: gist.bash, gist-fzf.bash, and gist-fzsl.bash. The first
provides simple tab completion and can be enable by adding the following to
your .bashrc file,

::

  source /usr/local/share/gist/gist.bash

The other scripts, gist-fzf.bash and fist-fzsl.bash, provide fuzzy matching of
gists using an ncurses interface (NB: these scripts require
`fzf <https://github.com/junegunn/fzf>`_ and `fzsl <https://github.com/jsbronder/fzsl>`_,
respectively).

The gist.fish script provides tab completion for the fish shell, and should be
copied to ~/.config/fish/completions.

The gist.zsh script provides tab completion for the zsh shell, and should be
copied to ~/.zsh as _gist. If not already in your ~/.zshrc file, you should add

::

  fpath=(${HOME}/.zsh $fpath)

To check that 'gist' is operating correctly, you can run the unit tests with,

::

  $ make test

Note that running the unit tests requires `poetry <https://python-poetry.org/>`_
to be available on your PATH.


Getting started
--------------------------------------------------

'gist' requires a personal access token for authentication. To create a token,
go to https://github.com/settings/tokens. The token needs to then be added
to a 'gist' configuration file that should have the form,

::

  [gist]
  token: <enter token here>
  editor: <path to editor>

The editor field is optional. If the default editor is specified through some
other mechanism 'gist' will try to infer it. Otherwise, you can use the config
file to ensure that 'gist' uses the editor you want it to use.

If the token string begins with ``!`` the text following is interpreted as a
shell command which, when executed, prints the token to stdout. For example::

  [gist]
  token: !gpg --decrypt github-token.gpg

The configuration file must be in one of the following,

::

  ${XDG_DATA_HOME}/gist
  ${HOME}/.config/gist
  ${HOME}/.gist

If more than one of these files exist, this is also the order of preference,
i.e. a configuration that is found in the ``${XDG_DATA_HOME}`` directory will be
taken in preference to ``${HOME}/.config/gist``.

Also, 'gist' assumes that you have set up your github account to use SSH keys so
that you can access your repositories without needing to provide a password.
Here__ is a link on setting up SSH keys with github.

__ https://help.github.com/articles/connecting-to-github-with-ssh/


Usage
--------------------------------------------------

'gist' is intended to make it easy to manage and use github gists from the
command line. There are several commands available:

::

  gist create      - creates a new gist
  gist edit        - edit the files in your gist
  gist description - updates the description of your gist
  gist list        - prints a list of your gists
  gist clone       - clones a gist
  gist delete      - deletes a gist or list of gists from github
  gist files       - prints a list of the files in a gist
  gist archive     - downloads a gist and creates a tarball
  gist content     - prints the content of the gist to stdout
  gist info        - prints detailed information about a gist
  gist version     - prints the current version
  gist help        - prints the help documentation


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

In addition to creating gists using the above methods, it is also possible to
encrypt a gist if you have gnupg installed. Any of the above methods can be used
to create encrypted gists by simply adding the --encrypt flag to invocation.
For example,

::

  $ gist create "arcana imperii" --encrypt

will open the editor allowing you to create the content of the gist, which is
then encrypted and added to github. See the Configuration section for
information on how to enable gnupg support.


**gist edit**

You can edit your gists directly with the 'edit' command. This command will
clone the gist to a temporary directory and open up the default editor (defined
by the EDITOR environment variable) to edit the files in the gist. When the
editor is exited the user is prompted to commit the changes, which are then
pushed back to the remote.

**gist description**

You can update the description of your gist with the 'description' command.
You need to supply the gist ID and the new description. For example -

::

  $ gist description e1f5e95a1705cbfde144 "This is a new description"


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

Deletes the specified gists from github.


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

If a filename is given, only the content of the specified filename will be
printed.

::

  $ gist content de42344a4ecb6250d6cea00d9da6d83a file1
  content of file 1


If the contents of the gist is encrypted, it can be viewed in its decrypted
form by adding the --decrypt flag, e.g.

::

  $ gist content --decrypt 8fe557fb3771aa74edfd
  foo.txt.asc (decrypted):
  this is a secret


See the Configuration section for information on how to enable gnupg support.


**gist info**

This command provides a complete dump of the information about the gist as a
JSON object. It is mostly useful for debugging.


**gist version**

Simply prints the current version.


**gist help**

Prints out the help documentation.


Configuration
--------------------------------------------------

There are several parameters that can be added to a configuration file to
determine the behavior of gist. The configuration file itself is expected to
be one of the following paths,

::

  ${HOME}/.gist
  ${HOME}/.config/gist
  ${XDG_DATA_HOME}/gist

The configuration file follows the .ini style. The following is an example,

::

  [gist]
  token: dde7b84d1e0edf7454ab354934b6ab36b01bf00f
  editor: /usr/bin/vim
  gnupg-homedir: /home/user/.gnupg
  gnupg-fingerprint: 179F9650D9FC1BFE391620B4B13A7829D8DE8623
  delete-tempfiles: False

The only essential field in the configuration file is the token. This is the
authentication token from github that grants gist permission to access your
gists. The editor is the editor to use if the EDITOR environment is not set or
you wish to use a different editor. 'gnupg-homedir' is the directory where your
gnupg data are stored, and 'gnupg-fingerprint' is the fingerprint of the key to
use to encrypt data in your gists. Both gnupg fields are required to support
encryption/decryption.

The 'delete-tempfiles' option is used when gists are created from an editor.
The editor writes its contents to a temporary file, which is deleted by
default. The default behavior can be overridden by using the 'delete-tempfiles'
flag.


Contributors
--------------------------------------------------

Thank you to the following people for contributing to 'gist'!

* Eren Inan Canpolat (https://github.com/canpolat)
* Kaan Genç (https://github.com/SeriousBug)
* Eric James Michael Ritz (https://github.com/ejmr)
* Karan Parikh (https://github.com/karanparikh)
* Konstantin Krastev (https://github.com/grizmin)
* Brandon Davidson (https://github.com/brandond)
* jq170727 (https://github.com/jq170727)
* jsbronder (https://github.com/jsbronder)
* hugsy (https://github.com/hugsy)
* Kenneth Benzie (https://github.com/kbenzie)
* rtfmoz2 (https://github.com/rtfmoz2)
