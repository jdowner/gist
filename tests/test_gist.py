import base64
import configparser
import errno
import gnupg
import json
import re
import shlex
import subprocess
import sys

import gist
import gist.client
import pytest
import responses


def b64encode(s):
    """Return the base64 encoding of a string

    To support string encodings other than ascii, the content of a gist needs
    to be uploaded in base64. Because python2.x and python3.x handle string
    differently, it is necessary to be explicit about passing a string into
    b64encode as bytes. This function handles the encoding of the string into
    bytes, and then decodes the resulting bytes into a UTF-8 string, which is
    returned.

    """
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")


@responses.activate
def test_list(gist_api):
    responses.add(
        responses.GET,
        "https://api.github.com/gists",
        body=json.dumps(
            [
                {
                    "id": 1,
                    "description": "test-desc-A",
                    "public": True,
                },
                {
                    "id": 2,
                    "description": "test-desc-\u212C",
                    "public": False,
                },
            ]
        ),
        status=200,
    )

    gists = gist_api.list()

    gistA = gists[0]
    gistB = gists[1]

    assert gistA.id == 1
    assert gistA.desc == "test-desc-A"
    assert gistA.public

    assert gistB.id == 2
    assert gistB.desc == "test-desc-\u212C"
    assert not gistB.public


@responses.activate
def test_list_empty(gist_api):
    responses.add(
        responses.GET,
        "https://api.github.com/gists",
        body="",
        status=200,
    )

    gists = gist_api.list()

    assert len(gists) == 0


@responses.activate
def test_content(gist_api):
    responses.add(
        responses.GET,
        "https://api.github.com/gists/1",
        body=json.dumps(
            {
                "files": {
                    "file-A.txt": {
                        "filename": "file-A.txt",
                        "content": b64encode("test-content-A"),
                    },
                    "file-B.txt": {
                        "filename": "file-B.txt",
                        "content": b64encode("test-content-\u212C"),
                    },
                },
                "description": "test-gist",
                "public": True,
                "id": 1,
            }
        ),
        status=200,
    )

    content = gist_api.content("1")

    assert len(content) == 2
    assert "file-A.txt" in content
    assert "file-B.txt" in content
    assert content["file-A.txt"] == "test-content-A"
    assert content["file-B.txt"] == "test-content-\u212C"


@responses.activate
def test_create(gist_api):
    def request_handler(request):
        data = json.loads(request.body)
        assert len(data["files"]) == 2
        assert "test-file-A" in data["files"]

        content = {k: v["content"] for k, v in data["files"].items()}

        assert content["test-file-A"] == "test-content-A"
        assert content["test-file-B"] == "test-content-\u212C"

        status = 200
        headers = {}
        body = json.dumps({"html_url": "https://gist.github.com/gists/1"})
        return status, headers, body

    responses.add_callback(
        responses.POST,
        "https://api.github.com/gists",
        callback=request_handler,
        content_type="application/json",
    )

    public = True
    desc = "test-desc"
    files = {
        "test-file-A": {"content": "test-content-A"},
        "test-file-B": {"content": "test-content-\u212C"},
    }

    gist_api.create(desc, files, public)


@responses.activate
def test_gnupg_create_from_file(decrypt, gist_command, tmp_path):
    """
    This test checks that the content from a gist created from a file is
    properly encrypted.

    """

    def request_handler(request):
        # Decrypt the content of the request and check that it matches the
        # original content.
        body = json.loads(request.body)
        data = list(body["files"].values())
        text = decrypt(data[0]["content"])

        assert u"test-content-\u212C" in text

        status = 200
        headers = {}
        body = json.dumps({"html_url": "https://gist.github.com/gists/1"})

        return status, headers, body

    responses.add_callback(
        responses.POST,
        "https://api.github.com/gists",
        callback=request_handler,
        content_type="application/json",
    )

    # Create a temporary file and write a test message to it
    filename = tmp_path / "gist-test-file.txt"
    with open(filename, "w", encoding="utf-8") as fp:
        fp.write(u"test-content-\u212C\n")

    # It is important to escape the path here to ensure the separators are not stripped
    # on Windows.
    cmd = r'create --encrypt "test-desc" {}'.format(re.escape(str(filename)))

    gist_command(cmd)


@responses.activate
def test_gnupg_content(encrypt, gist_command):
    """
    When encrypted content is received, check to make sure that it can be
    properly decrypted.

    """

    def b64encrypt(content):
        return b64encode(encrypt(content))

    responses.add(
        responses.GET,
        "https://api.github.com/gists/1",
        body=json.dumps(
            {
                "files": {
                    "file-A.txt": {
                        "filename": "file-A.txt",
                        "content": b64encrypt(u"test-content-A"),
                    },
                    "file-B.txt": {
                        "filename": "file-B.txt",
                        "content": b64encrypt(u"test-content-\u212C"),
                    },
                },
                "description": "test-gist",
                "public": True,
                "id": 1,
            }
        ),
        status=200,
    )

    lines = gist_command("content 1 --decrypt")

    assert u"file-A.txt (decrypted):" in lines
    assert u"test-content-A" in lines
    assert u"file-B.txt (decrypted):" in lines
    assert u"test-content-\u212C" in lines


def test_gnupg(encrypt, decrypt):
    """
    Make sure that the basic mechanism put in place for testing the
    encryption used in gist works as expected.

    """
    text = u"this is a message \u212C"
    cypher = encrypt(text)
    plain = decrypt(cypher)

    assert text != cypher
    assert text == plain
