import configparser

import gist
import pytest


@pytest.fixture
def config():
    cfg = configparser.ConfigParser()
    cfg.add_section("gist")
    return cfg


def test_get_value_from_command():
    """
    Ensure that values which start with ``!`` are treated as commands and
    return the string printed to stdout by the command, otherwise ensure
    that the value passed to the function is returned.
    """
    assert "magic token" == gist.client.get_value_from_command('!echo "\nmagic token"')
    assert "magic token" == gist.client.get_value_from_command(' !echo "magic token\n"')
    assert "magic token" == gist.client.get_value_from_command("magic token")


def test_get_personal_access_token_missing(config):
    with pytest.raises(gist.client.GistMissingTokenError):
        gist.client.get_personal_access_token(config)


@pytest.mark.parametrize("token", ["", "   "])
def test_get_personal_access_token_empty(config, token):
    config.set("gist", "token", token)
    with pytest.raises(gist.client.GistEmptyTokenError):
        gist.client.get_personal_access_token(config)


@pytest.mark.parametrize("token", ["   123   ", "123abcABC0987"])
def test_get_personal_access_token_valid(config, token):
    config.set("gist", "token", token)
    gist.client.get_personal_access_token(config)
