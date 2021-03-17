import base64
import json

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
def test_list(editor, gist_command):
    message = list()
    expected_gists = list()
    for id in range(300):
        desc = "test-{}".format(id)
        public = id % 2 == 0

        message.append(
            {
                "id": id,
                "description": desc,
                "public": public,
            }
        )

        expected_gists.append("{} {} test-{}".format(id, "+" if public else "-", id))

    responses.add(
        responses.GET,
        "https://api.github.com/gists",
        body=json.dumps(message),
        status=200,
    )

    gists = gist_command("list")

    assert gists == expected_gists


@responses.activate
def test_content(editor, gist_command):
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

    lines = gist_command("content 1")

    assert "file-A.txt:" in lines
    assert "test-content-A" in lines
    assert "file-B.txt:" in lines
    assert "test-content-\u212c" in lines
