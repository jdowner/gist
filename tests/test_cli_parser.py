import shlex
import unittest.mock

import gist.client
import pytest


@pytest.mark.parametrize(
    "command",
    [
        "create 'desc'",
        "create --public 'desc'",
        "create --encrypt 'desc'",
        "create --public --encrypt 'desc'",
        "create --public --encrypt 'desc' --filename file1",
        "create --public --encrypt 'desc' file1 file2 file3",
        "create 'desc' --public",
        "create 'desc' --encrypt",
        "create 'desc' --public --encrypt",
    ],
)
def test_cli_parser_gist_create_valid(monkeypatch, command):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_create", handler)

    gist.client.main(argv=shlex.split(command))


@pytest.mark.parametrize(
    "command",
    [
        "create --public",
        "create --encrypt",
        "create 'desc' --encrypt file1",
        "create --public --encrypt 'desc' --filename file1 file2",
    ],
)
def test_cli_parser_gist_create_invalid(monkeypatch, command):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_create", handler)

    with pytest.raises(SystemExit):
        gist.client.main(argv=shlex.split(command))


def test_cli_parser_gist_list_valid(monkeypatch):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_list", handler)

    gist.client.main(argv=shlex.split("list"))


def test_cli_parser_gist_list_invalid(monkeypatch):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_list", handler)

    with pytest.raises(SystemExit):
        gist.client.main(argv=shlex.split("list --no-an-option"))


@pytest.mark.parametrize("cmd", ["edit", "fork", "info", "files", "archive"])
def test_cli_parser_gist_generic_valid(monkeypatch, cmd):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_{}".format(cmd), handler)

    gist.client.main(argv=shlex.split("{} arg1".format(cmd)))


@pytest.mark.parametrize("args", ["", "arg1 arg2"])
@pytest.mark.parametrize("cmd", ["edit", "fork", "info", "files", "archive"])
def test_cli_parser_gist_generic_invalid(monkeypatch, cmd, args):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_{}".format(cmd), handler)

    with pytest.raises(SystemExit):
        gist.client.main(argv=shlex.split("{} {}".format(cmd, args)))


@pytest.mark.parametrize("command", ["description id desc", "description id 'desc'"])
def test_cli_parser_gist_description_valid(monkeypatch, command):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_description", handler)

    gist.client.main(argv=shlex.split(command))


@pytest.mark.parametrize(
    "command",
    [
        "description id",
        "description id foo bar",
    ],
)
def test_cli_parser_gist_description_invalid(monkeypatch, command):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_description", handler)

    with pytest.raises(SystemExit):
        gist.client.main(argv=shlex.split(command))


@pytest.mark.parametrize(
    "command",
    [
        "content id",
        "content id --decrypt",
        "content id file1 --decrypt",
        "content --decrypt id",
        "content --decrypt id file1",
    ],
)
def test_cli_parser_gist_content_valid(monkeypatch, command):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_content", handler)

    gist.client.main(argv=shlex.split(command))


@pytest.mark.parametrize(
    "command",
    [
        "content",
        "content --decrypt",
        "content id file1 file2 --decrypt",
    ],
)
def test_cli_parser_gist_content_invalid(monkeypatch, command):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_content", handler)

    with pytest.raises(SystemExit):
        gist.client.main(argv=shlex.split(command))


@pytest.mark.parametrize(
    "command",
    [
        "clone id",
        "clone id name",
        "clone id 'long name'",
    ],
)
def test_cli_parser_gist_clone_valid(monkeypatch, command):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_clone", handler)

    gist.client.main(argv=shlex.split(command))


@pytest.mark.parametrize("command", ["clone", "clone id name1 name2"])
def test_cli_parser_gist_clone_invalid(monkeypatch, command):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_clone", handler)

    with pytest.raises(SystemExit):
        gist.client.main(argv=shlex.split(command))


def test_cli_parser_gist_version_valid(monkeypatch):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_version", handler)

    gist.client.main(argv=shlex.split("version"))


def test_cli_parser_gist_version_invalid(monkeypatch):
    handler = unittest.mock.Mock()
    monkeypatch.setattr(gist.client, "handle_gist_version", handler)

    with pytest.raises(SystemExit):
        gist.client.main(argv=shlex.split("version arg"))
