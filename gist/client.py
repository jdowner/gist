#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Name:
    gist

Usage:
    gist help
    gist list
    gist edit <id>
    gist description <id> <desc>
    gist info <id>
    gist fork <id>
    gist files <id>
    gist delete <ids> ...
    gist archive <id>
    gist content <id> [<filename>] [--decrypt]
    gist create <desc> [--public] [--encrypt] [FILES ...]
    gist create <desc> [--public] [--encrypt] [--filename <filename>]
    gist clone <id> [<name>]
    gist version

Description:
    This program provides a command line interface for interacting with github
    gists.

Commands:
    help
        Shows this documentation.

    create
        Create a new gist. A gist can be created in several ways. The content
        of the gist can be piped to the gist,

            $ echo "this is the content" | gist create "gist description"

        The gist can be created from an existing set of files,

            $ gist create "gist description" foo.txt bar.txt

        The gist can be created on the fly,

            $ gist create "gist description"

        which will open the users default editor.

        If you are creating a gist with a single file using either the pipe or
        'on the fly' method above, you can also supply an optional argument to
        name the file instead of using the default ('file1.txt'),

            $ gist create "gist description" --filename foo.md

        Note that the use of --filename is incompatible with passing in a list
        of existing files.

    edit
        You can edit your gists directly with the 'edit' command. This command
        will clone the gist to a temporary directory and open up the default
        editor (defined by the EDITOR environment variable) to edit the files
        in the gist. When the editor is exited the user is prompted to commit
        the changes, which are then pushed back to the remote.

    fork
        Creates a fork of the specified gist.

    description
        Updates the description of a gist.

    list
        Returns a list of your gists. The gists are returned as,

            2b1823252e8433ef8682 - mathematical divagations
            a485ee9ddf6828d697be - notes on defenestration
            589071c7a02b1823252e + abecedarian pericombobulations

        The first column is the gists unique identifier; The second column
        indicates whether the gist is public ('+') or private ('-'); The third
        column is the description in the gist, which may be empty.

    clone
        Clones a gist to the current directory. This command will clone any
        gist based on its unique identifier (i.e. not just the users) to the
        current directory.

    delete
        Deletes the specified gist.

    files
        Returns a list of the files in the specified gist.

    archive
        Downloads the specified gist to a temporary directory and adds it to a
        tarball, which is then moved to the current directory.

    content
        Writes the content of each file in the specified gist to the terminal,
        e.g.

            $ gist content c971fca7997aed65ddc9
            foo.txt:
            this is foo


            bar.txt:
            this is bar


        For each file in the gist the first line is the name of the file
        followed by a colon, and then the content of that file is written to
        the terminal.

        If a filename is given, only the content of the specified filename
        will be printed.

           $ gist content de42344a4ecb6250d6cea00d9da6d83a file1
           content of file 1


    info
        This command provides a complete dump of the information about the gist
        as a JSON object. It is mostly useful for debugging.

    version
        Returns the current version of gist.

"""

import argparse
import codecs
import collections
import configparser
import json
import locale
import logging
import os
import pathlib
import platform
import shlex
import struct
import subprocess
import sys
import tempfile

import gnupg

from . import gist
from . import version

if platform.system() != "Windows":
    # those modules exist everywhere but on Windows
    import termios
    import fcntl


logger = logging.getLogger("gist")


def wrap_stdout_for_unicode():
    """
    We need to wrap stdout in order to properly handle piping unicode output.
    However, detaching stdout can cause problems when trying to run tests.
    Therefore this logic is placed inside this function so that it can be
    disabled (monkeypatched) when tests are run.
    """

    encoding = locale.getpreferredencoding()
    sys.stdout = codecs.getwriter(encoding)(sys.stdout.detach())


class GistError(Exception):
    def __init__(self, msg):
        super(GistError, self).__init__(msg)
        self.msg = msg


class GistMissingTokenError(GistError):
    pass


class GistEmptyTokenError(GistError):
    pass


class UserError(Exception):
    pass


class FileInfo(collections.namedtuple("FileInfo", "name content")):
    pass


def terminal_width():
    """Returns the terminal width

    Tries to determine the width of the terminal. If there is no terminal, then
    None is returned instead.

    """
    try:
        if platform.system() == "Windows":
            from ctypes import windll, create_string_buffer

            # Reference: https://docs.microsoft.com/en-us/windows/console/getstdhandle # noqa
            hStdErr = -12
            get_console_info_fmtstr = "hhhhHhhhhhh"
            herr = windll.kernel32.GetStdHandle(hStdErr)
            csbi = create_string_buffer(struct.calcsize(get_console_info_fmtstr))
            if not windll.kernel32.GetConsoleScreenBufferInfo(herr, csbi):
                raise OSError("Failed to determine the terminal size")
            (_, _, _, _, _, left, top, right, bottom, _, _) = struct.unpack(
                get_console_info_fmtstr, csbi.raw
            )
            tty_columns = right - left + 1
            return tty_columns
        else:
            exitcode = fcntl.ioctl(
                0, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0)
            )
            h, w, hp, wp = struct.unpack("HHHH", exitcode)
        return w
    except Exception:
        pass


def elide(txt):
    """Elide the text to the width of the current terminal.

    Arguments:
        txt: the string to potentially elide

    Returns:
        A string that is no longer than the specified width.

    """
    width = terminal_width()
    if width is not None and width > 3:
        try:
            if len(txt) > width:
                return txt[: width - 3] + "..."
        except Exception:
            pass

    return txt


def get_value_from_command(value):
    """Return the value of a config option, potentially by running a command

    When a config option begins with a ``!`` interpret the remaining text as a
    shell command which when run prints the config option value to stdout.
    Otherwise return the original string.

    Argument:
        value: value of an option returned from the config file.

    """
    command = value.strip()
    if command[0] == "!":
        process = subprocess.Popen(
            shlex.split(command[1:]), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = process.communicate()
        if process.returncode != 0:
            raise GistError(err)
        return out.decode().strip()
    return value


def get_personal_access_token(config):
    """Returns the users personal access token

    Argument:
        config: a configuration object

    """
    try:
        value = config.get("gist", "token").strip()
        if not value:
            raise GistEmptyTokenError("An empty token is not valid")

    except configparser.NoOptionError:
        raise GistMissingTokenError("Missing 'token' field in configuration")

    return get_value_from_command(value)


def alternative_editor(default):
    """Return the path to the 'alternatives' editor

    Argument:
        default: the default to use if the alternatives editor cannot be found.

    """
    if os.path.exists("/usr/bin/editor"):
        return "/usr/bin/editor"

    return default


def environment_editor(default):
    """Return the user specified environment default

    Argument:
        default: the default to use if the environment variable contains
                nothing useful.

    """
    editor = os.environ.get("EDITOR", "").strip()
    if editor != "":
        return editor

    return default


def configuration_editor(config, default):
    """Return the editor in the config file

    Argument:
        default: the default to use if there is no editor in the config

    """
    try:
        return config.get("gist", "editor")
    except configparser.NoOptionError:
        return default


def homedir_config(default):
    """Return the path to the config file in the users home directory

    Argument:
        default: the default to use if ~/.gist does not exist.

    """
    config_path = pathlib.Path("~").expanduser() / ".gist"
    return config_path if config_path.is_file() else default


def alternative_config(default):
    """Return the path to the config file in .config directory

    Argument:
        default: the default to use if ~/.config/gist does not exist.

    """
    config_path = pathlib.Path("~/.config/gist").expanduser()
    return config_path if config_path.is_file() else default


def xdg_data_config(default):
    """Return the path to the config file in XDG user config directory

    Argument:
        default: the default to use if either the XDG_DATA_HOME environment is
            not set, or the XDG_DATA_HOME directory does not contain a 'gist'
            file.

    """
    config_path = os.environ.get("XDG_DATA_HOME", None)
    if config_path is not None:
        config_path = pathlib.Path(config_path) / "gist"
        if config_path.is_file():
            return config_path

    return default


def environment_config(default):
    """Return the path to the config file defined in an environment variable

    Argument:
        default: the default to use if the environment variable GIST_CONFIG has not been
        set.

    """
    config_path = os.environ.get("GIST_CONFIG", None)
    if config_path is not None:
        config_path = pathlib.Path(config_path)
        if config_path.is_file():
            return config_path

    return default


def load_config_file():
    """
    Returns a ConfigParser object with any gist related configuration data
    """

    config = configparser.ConfigParser()

    config_path = homedir_config(None)
    config_path = alternative_config(config_path)
    config_path = xdg_data_config(config_path)
    config_path = environment_config(config_path)

    if config_path is None:
        raise UserError("unable to find config file")

    try:
        with open(config_path) as fp:
            config.read_file(fp)

    except Exception as e:
        raise UserError("Unable to load configuration file: {0}".format(e))

    # Make sure the config contains a gist section. If it does not, create one so
    # that the following code can simply assume it exists.
    if not config.has_section("gist"):
        config.add_section("gist")

    return config


def handle_gist_list(gapi, args, *vargs):
    """Handle 'gist list' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments

    """
    logger.debug(u"action: list")
    gists = gapi.list()
    for info in gists:
        public = "+" if info.public else "-"
        desc = "" if info.desc is None else info.desc
        line = u"{} {} {}".format(info.id, public, desc)
        try:
            print(elide(line))
        except UnicodeEncodeError:
            logger.error("unable to write gist {}".format(info.id))


def handle_gist_edit(gapi, args, *vargs):
    """Handle 'gist edit' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments

    """
    logger.debug(u"action: edit")
    logger.debug(u"action: - {}".format(args.id))
    gapi.edit(args.id)


def handle_gist_description(gapi, args, *vargs):
    """Handle 'gist description' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments

    """
    logger.debug(u"action: description")
    logger.debug(u"action: - {}".format(args.id))
    logger.debug(u"action: - {}".format(args.desc))
    gapi.description(args.id, args.desc)


def handle_gist_info(gapi, args, *vargs):
    """Handle 'gist info' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments

    """
    logger.debug(u"action: info")
    logger.debug(u"action: - {}".format(args.id))
    info = gapi.info(args.id)
    print(json.dumps(info, indent=2))


def handle_gist_fork(gapi, args, *vargs):
    """Handle 'gist fork' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments

    """
    logger.debug(u"action: fork")
    logger.debug(u"action: - {}".format(args.id))
    _ = gapi.fork(args.id)


def handle_gist_files(gapi, args, *vargs):
    """Handle 'gist files' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments

    """
    logger.debug(u"action: files")
    logger.debug(u"action: - {}".format(args.id))
    for f in gapi.files(args.id):
        print(f)


def handle_gist_delete(gapi, args, *vargs):
    """Handle 'gist delete' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments

    """
    logger.debug(u"action: delete")
    for gist_id in args.ids:
        logger.debug(u"action: - {}".format(gist_id))
        gapi.delete(gist_id)


def handle_gist_archive(gapi, args, *vargs):
    """Handle 'gist archive' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments

    """
    logger.debug(u"action: archive")
    logger.debug(u"action: - {}".format(args.id))
    gapi.archive(args.id)


def handle_gist_content(gapi, args, config, *vargs):
    """Handle 'gist content' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments
        config: configuration data

    """
    logger.debug(u"action: content")
    logger.debug(u"action: - {}".format(args.id))

    content = gapi.content(args.id)
    gist_file = content.get(args.filename)

    if args.decrypt:
        if not config.has_option("gist", "gnupg-homedir"):
            raise GistError("gnupg-homedir missing from config file")

        homedir = config.get("gist", "gnupg-homedir")
        logger.debug(u"action: - {}".format(homedir))

        gpg = gnupg.GPG(gnupghome=homedir, use_agent=True)
        if gist_file is not None:
            print(gpg.decrypt(gist_file).data.decode("utf-8"))
        else:
            for name, lines in content.items():
                lines = gpg.decrypt(lines).data.decode("utf-8")
                print(u"{} (decrypted):\n{}\n".format(name, lines))

    else:
        if gist_file is not None:
            print(gist_file)
        else:
            for name, lines in content.items():
                print(u"{}:\n{}\n".format(name, lines))


def handle_gist_create(gapi, args, config, editor, *vargs):
    """Handle 'gist create' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments
        config: configuration data
        editor: editor command to use to create gist content

    """
    logger.debug("action: create")

    # If encryption is selected, perform an initial check to make sure that
    # it is possible before processing any data.
    if args.encrypt:
        if not config.has_option("gist", "gnupg-homedir"):
            raise GistError("gnupg-homedir missing from config file")

        if not config.has_option("gist", "gnupg-fingerprint"):
            raise GistError("gnupg-fingerprint missing from config file")

    # Retrieve the data to add to the gist
    files = list()

    if sys.stdin.isatty():
        if args.files:
            logger.debug("action: - reading from files")
            for path in args.files:
                name = os.path.basename(path)
                with open(path, "rb") as fp:
                    files.append(FileInfo(name, fp.read().decode("utf-8")))

        else:
            logger.debug("action: - reading from editor")

            filename = "file1.txt" if args.filename is None else args.filename

            # Determine whether the temporary file should be deleted
            if config.has_option("gist", "delete-tempfiles"):
                delete = config.getboolean("gist", "delete-tempfiles")
            else:
                delete = True

            with tempfile.NamedTemporaryFile("wb+", delete=delete) as fp:
                logger.debug("action: - created {}".format(fp.name))
                os.system("{} {}".format(editor, fp.name))
                fp.flush()
                fp.seek(0)

                files.append(FileInfo(filename, fp.read().decode("utf-8")))

            if delete:
                logger.debug("action: - removed {}".format(fp.name))

    else:
        logger.debug("action: - reading from stdin")

        filename = "file1.txt" if args.filename is None else args.filename
        files.append(FileInfo(filename, sys.stdin.read()))

    # Ensure that there are no empty files
    for file in files:
        if len(file.content) == 0:
            raise GistError("'{}' is empty".format(file.name))

    # Encrypt the files or leave them unmodified
    if args.encrypt:
        logger.debug("action: - encrypting content")

        fingerprint = config.get("gist", "gnupg-fingerprint")
        gnupghome = config.get("gist", "gnupg-homedir")

        gpg = gnupg.GPG(gnupghome=gnupghome, use_agent=True)
        data = {}
        for file in files:
            cypher = gpg.encrypt(file.content.encode("utf-8"), fingerprint)
            content = cypher.data.decode("utf-8")

            data["{}.asc".format(file.name)] = {"content": content}
    else:
        data = {file.name: {"content": file.content} for file in files}

    print(gapi.create(args.desc, data, args.public))


def handle_gist_clone(gapi, args, *vargs):
    """Handle 'gist clone' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments

    """
    logger.debug(u"action: clone")
    logger.debug(u"action: - {} as {}".format(args.id, args.name))
    gapi.clone(args.id, args.name)


def handle_gist_version(gapi, args, *vargs):
    """Handle 'gist version' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments

    """
    logger.debug(u"action: version")
    print("v{}".format(version.__version__))


def handle_gist_help(gapi, args, *vargs):
    """Handle 'gist help' command

    Arguments:
        gapi: a GistAPI object
        args: parsed command line arguments

    """
    logger.debug(u"action: help")
    print(__doc__)


def create_gist_list_parser(subparser):
    """Create parser for 'gist list' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("list")
    parser.set_defaults(func=handle_gist_list)


def create_gist_edit_parser(subparser):
    """Create parser for 'gist edit' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("edit")
    parser.add_argument("id")
    parser.set_defaults(func=handle_gist_edit)


def create_gist_description_parser(subparser):
    """Create parser for 'gist description' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("description")
    parser.add_argument("id")
    parser.add_argument("desc")
    parser.set_defaults(func=handle_gist_description)


def create_gist_info_parser(subparser):
    """Create parser for 'gist info' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("info")
    parser.add_argument("id")
    parser.set_defaults(func=handle_gist_info)


def create_gist_fork_parser(subparser):
    """Create parser for 'gist fork' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("fork")
    parser.add_argument("id")
    parser.set_defaults(func=handle_gist_fork)


def create_gist_files_parser(subparser):
    """Create parser for 'gist files' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("files")
    parser.add_argument("id")
    parser.set_defaults(func=handle_gist_files)


def create_gist_delete_parser(subparser):
    """Create parser for 'gist delete' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("delete")
    parser.add_argument("ids", nargs="+")
    parser.set_defaults(func=handle_gist_delete)


def create_gist_archive_parser(subparser):
    """Create parser for 'gist archive' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("archive")
    parser.add_argument("id")
    parser.set_defaults(func=handle_gist_archive)


def create_gist_content_parser(subparser):
    """Create parser for 'gist content' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("content")
    parser.add_argument("id")
    parser.add_argument("filename", nargs="?", default=None)
    parser.add_argument("--decrypt", action="store_true")
    parser.set_defaults(func=handle_gist_content)


def create_gist_create_parser(subparser):
    """Create parser for 'gist create' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("create")
    parser.add_argument("desc")
    parser.add_argument("--encrypt", action="store_true")
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--filename")
    parser.add_argument("files", nargs="*")
    parser.set_defaults(func=handle_gist_create)


def create_gist_clone_parser(subparser):
    """Create parser for 'gist clone' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("clone")
    parser.add_argument("id")
    parser.add_argument("name", nargs="?", default=None)
    parser.set_defaults(func=handle_gist_clone)


def create_gist_version_parser(subparser):
    """Create parser for 'gist version' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("version")
    parser.set_defaults(func=handle_gist_version)


def create_gist_help_parser(subparser):
    """Create parser for 'gist help' command

    Arguments:
        subparser: subparser object from primary parser

    """
    parser = subparser.add_parser("help")
    parser.set_defaults(func=handle_gist_help)


def create_gist_parser():
    """Create main parser for 'gist' commands"""

    # Subclass the ArgumentParser so that we can override the 'error' function
    class Parser(argparse.ArgumentParser):
        def __init__(self, *args, **kwargs):
            kwargs["add_help"] = False
            super().__init__(*args, **kwargs)

        def error(self, message):
            raise UserError(message)

    parser = Parser()
    subparser = parser.add_subparsers()

    create_gist_list_parser(subparser)
    create_gist_edit_parser(subparser)
    create_gist_description_parser(subparser)
    create_gist_info_parser(subparser)
    create_gist_fork_parser(subparser)
    create_gist_files_parser(subparser)
    create_gist_delete_parser(subparser)
    create_gist_archive_parser(subparser)
    create_gist_content_parser(subparser)
    create_gist_create_parser(subparser)
    create_gist_clone_parser(subparser)
    create_gist_version_parser(subparser)
    create_gist_help_parser(subparser)

    return parser


def main(argv=sys.argv[1:], config=None):
    try:
        wrap_stdout_for_unicode()

        # Setup logging
        fmt = "%(created).3f %(levelname)s[%(name)s] %(message)s"
        logging.basicConfig(format=fmt)

        # Read in the configuration file
        if config is None:
            config = load_config_file()

        try:
            log_level = config.get("gist", "log-level").upper()
            logging.getLogger("gist").setLevel(log_level)
        except Exception:
            logging.getLogger("gist").setLevel(logging.ERROR)

        # Determine the editor to use
        editor = None
        editor = alternative_editor(editor)
        editor = environment_editor(editor)
        editor = configuration_editor(config, editor)

        if editor is None:
            raise UserError("Unable to find an editor.")

        token = get_personal_access_token(config)
        gapi = gist.GistAPI(token=token, editor=editor)

        # Parser command line arguments
        parser = create_gist_parser()
        args = parser.parse_args(argv)
        args.func(gapi, args, config, editor)

    except UserError as e:
        sys.stderr.write(u"ERROR: {}\n".format(str(e)))
        sys.stderr.flush()
        sys.exit(1)
    except GistError as e:
        sys.stderr.write(u"GIST: {}\n".format(e.msg))
        sys.stderr.flush()
        sys.exit(1)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
