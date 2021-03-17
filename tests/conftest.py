import configparser
import errno
import shlex
import subprocess

import gist.client
import gist.gist
import gnupg
import pytest


def kill_gpg_agent(homedir):
    """Try to kill the spawned gpg-agent

    This is just a best-effort.  With gpg-1.x, the agent will most likely not
    get started unless the user has done configuration to enforce it.  With
    gpg-2.x, the agent will always be spawned as it is responsible for all
    handling of private keys.  However, it was not until gpg-2.1.13 that
    gpgconf accepted the homedir argument.

    So:
        - gpg-1.x probably has nothing to kill and the return value doesn't
          matter
        - <gpg-2.1.13 will leave an agent running after the tests exit
        - >=gpg-2.1.13 will correctly kill the agent on shutdown.

    This could be improved, but 2.1.13 was released in mid-2016 and a quick
    survey of distros using gpg-2 shows they've all moved past that point.

    """
    try:
        subprocess.call(
            shlex.split("gpgconf --homedir {} --kill gpg-agent".format(homedir))
        )
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


@pytest.fixture(autouse=True)
def disable_stdout_wrapper(monkeypatch):
    monkeypatch.setattr(gist.client, "wrap_stdout_for_unicode", lambda: None)


@pytest.fixture(autouse=True)
def editor(monkeypatch):
    monkeypatch.setenv("EDITOR", "gist-placeholder")


@pytest.fixture
def gist_api():
    return gist.gist.GistAPI(token="f00")


@pytest.fixture
def gnupghome():
    return "./tests/gnupg"


@pytest.fixture
def gpg(gnupghome):
    try:
        yield gnupg.GPG(gnupghome=gnupghome, use_agent=True)
    finally:
        kill_gpg_agent(gnupghome)


@pytest.fixture
def fingerprint(gpg):
    return gpg.list_keys()[0]["fingerprint"]


@pytest.fixture
def encrypt(gpg, fingerprint):
    def impl(text):
        data = text.encode("utf-8")
        crypt = gpg.encrypt(data, fingerprint)
        return crypt.data.decode("utf-8")

    return impl


@pytest.fixture
def decrypt(gpg):
    def impl(text):
        """Return the text as a decrypted string"""
        data = text.encode("utf-8")
        crypt = gpg.decrypt(data)
        return crypt.data.decode("utf-8")

    return impl


@pytest.fixture
def config(gnupghome, fingerprint):
    cfg = configparser.ConfigParser()
    cfg.add_section("gist")
    cfg.set("gist", "token", "f00")
    cfg.set("gist", "gnupg-homedir", gnupghome)
    cfg.set("gist", "gnupg-fingerprint", fingerprint)

    return cfg


@pytest.fixture
def gist_command(config, capsys):
    def impl(cmd):
        """Return stdout produce by the specified CLI command"""
        gist.client.main(argv=shlex.split(cmd), config=config)
        return capsys.readouterr().out.splitlines()

    return impl
