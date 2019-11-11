#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import contextlib
import errno
import gnupg
import os
import shlex
import subprocess
import sys
import tempfile
import unittest

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import json
import responses

import gist


# import the CLI script as a module of gist
import gist.client


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
    args = [
        'gpgconf',
        '--homedir',
        homedir,
        '--kill',
        'gpg-agent',
    ]
    try:
        subprocess.call(args)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


@contextlib.contextmanager
def redirect_stdout(buf):
    original = sys.stdout
    sys.stdout = buf
    yield
    sys.stdout = original


def b64encode(s):
    """Return the base64 encoding of a string

    To support string encodings other than ascii, the content of a gist needs
    to be uploaded in base64. Because python2.x and python3.x handle string
    differently, it is necessary to be explicit about passing a string into
    b64encode as bytes. This function handles the encoding of the string into
    bytes, and then decodes the resulting bytes into a UTF-8 string, which is
    returned.

    """
    return base64.b64encode(s.encode('utf-8')).decode('utf-8')


class TestGist(unittest.TestCase):
    @responses.activate
    def test_list(self):
        responses.add(responses.GET, 'https://api.github.com/gists',
                body=json.dumps([
                    {
                        'id': 1,
                        'description': 'test-desc-A',
                        'public': True,
                        },
                    {
                        'id': 2,
                        'description': 'test-desc-\u212C',
                        'public': False,
                        },
                    ]),
                status=200,
                )

        gists = gist.GistAPI(token="f00").list()

        gistA = gists[0]
        gistB = gists[1]

        self.assertEqual(gistA.id, 1)
        self.assertEqual(gistA.desc, 'test-desc-A')
        self.assertTrue(gistA.public)

        self.assertEqual(gistB.id, 2)
        self.assertEqual(gistB.desc, 'test-desc-\u212C')
        self.assertFalse(gistB.public)

    @responses.activate
    def test_list_empty(self):
        responses.add(responses.GET, 'https://api.github.com/gists',
                body="",
                status=200,
                )

        gists = gist.GistAPI(token="f00").list()

        self.assertTrue(len(gists) == 0)

    @responses.activate
    def test_content(self):
        responses.add(responses.GET, 'https://api.github.com/gists/1',
                body=json.dumps({
                    "files": {
                        "file-A.txt": {
                            "filename": "file-A.txt",
                            "content": b64encode("test-content-A"),
                            },
                        "file-B.txt": {
                            "filename": "file-B.txt",
                            "content": b64encode("test-content-\u212C"),
                            }
                        },
                    "description": "test-gist",
                    "public": True,
                    "id": 1,
                    }),
                status=200,
                )

        content = gist.GistAPI(token="f00").content("1")

        self.assertEqual(len(content), 2)
        self.assertTrue('file-A.txt' in content)
        self.assertTrue('file-B.txt' in content)
        self.assertEqual(content['file-A.txt'], 'test-content-A')
        self.assertEqual(content['file-B.txt'], 'test-content-\u212C')

    @responses.activate
    def test_create(self):
        def request_handler(request):
            data = json.loads(request.body)
            self.assertEqual(len(data['files']), 2)
            self.assertTrue('test-file-A' in data['files'])

            content = {k: v['content'] for k, v in data['files'].items()}

            self.assertEqual(content['test-file-A'], 'test-content-A')
            self.assertEqual(content['test-file-B'], 'test-content-\u212C')

            status = 200
            headers = {}
            body = json.dumps({
                'html_url': 'https://gist.github.com/gists/1'
                })
            return status, headers, body

        responses.add_callback(
                responses.POST,
                'https://api.github.com/gists',
                callback=request_handler,
                content_type='application/json',
                )

        public = True
        desc = 'test-desc'
        files = {
                'test-file-A': {'content': 'test-content-A'},
                'test-file-B': {'content': 'test-content-\u212C'},
                }

        gist.GistAPI(token="f00").create(desc, files, public)


class TestGistCLI(unittest.TestCase):
    def setUp(self):
        os.environ["EDITOR"] = "gist-placeholder"

        self.config = configparser.ConfigParser()
        self.config.add_section("gist")
        self.config.set("gist", "token", "f00")

    def command_response(self, cmd):
        buf = StringIO()
        with redirect_stdout(buf):
            gist.client.main(argv=shlex.split(cmd), config=self.config)

        return buf.getvalue().splitlines()

    @responses.activate
    def test_list(self):
        responses.add(responses.GET, 'https://api.github.com/gists',
                body=json.dumps([
                    {
                        'id': 1,
                        'description': 'test-desc-A',
                        'public': True,
                        },
                    {
                        'id': 2,
                        'description': 'test-desc-\u212C',
                        'public': False,
                        },
                    ]),
                status=200,
                )

        gists = self.command_response('list')
        gistA = gists[0]
        gistB = gists[1]

        self.assertEqual(gistA, '1 + test-desc-A')
        self.assertEqual(gistB, '2 - test-desc-\u212C')

    @responses.activate
    def test_content(self):
        def b64encode(s):
            return base64.b64encode(s.encode('utf-8')).decode('utf-8')

        responses.add(responses.GET, 'https://api.github.com/gists/1',
                body=json.dumps({
                    "files": {
                        "file-A.txt": {
                            "filename": "file-A.txt",
                            "content": b64encode("test-content-A"),
                            },
                        "file-B.txt": {
                            "filename": "file-B.txt",
                            "content": b64encode("test-content-\u212C"),
                            }
                        },
                    "description": "test-gist",
                    "public": True,
                    "id": 1,
                    }),
                status=200,
                )

        lines = self.command_response('content 1')

        self.assertIn('file-A.txt:', lines)
        self.assertIn('test-content-A', lines)
        self.assertIn('file-B.txt:', lines)
        self.assertIn('test-content-\u212C', lines)

    def test_get_value_from_command(self):
        """
        Ensure that values which start with ``!`` are treated as commands and
        return the string printed to stdout by the command, otherwise ensure
        that the value passed to the function is returned.
        """
        self.assertEqual(
            'magic token',
            gist.client.get_value_from_command('!echo "\nmagic token"'))
        self.assertEqual(
            'magic token',
            gist.client.get_value_from_command(' !echo "magic token\n"'))
        self.assertEqual(
            'magic token',
            gist.client.get_value_from_command('magic token'))


class TestGistGPG(unittest.TestCase):
    gnupghome = os.path.abspath('./tests/gnupg')

    def setUp(self):
        os.environ["EDITOR"] = "gist-placeholder"

        self.gpg = gnupg.GPG(gnupghome=self.gnupghome, use_agent=True)
        self.fingerprint = self.gpg.list_keys()[0]['fingerprint']

        self.config = configparser.ConfigParser()
        self.config.add_section("gist")
        self.config.set("gist", "token", "f00")
        self.config.set("gist", "gnupg-homedir", self.gnupghome)
        self.config.set("gist", "gnupg-fingerprint", self.fingerprint)

    @classmethod
    def tearDownClass(cls):
        kill_gpg_agent(cls.gnupghome)

    def command_response(self, cmd):
        """Return stdout produce by the specified CLI command"""
        buf = StringIO()
        with redirect_stdout(buf):
            gist.client.main(argv=shlex.split(cmd), config=self.config)

        return buf.getvalue().splitlines()

    def encrypt(self, text):
        """Return the text as an encrypted string"""
        data = text.encode('utf-8')
        crypt = self.gpg.encrypt(data, self.fingerprint)
        return crypt.data.decode('utf-8')

    def decrypt(self, text):
        """Return the text as a decrypted string"""
        data = text.encode('utf-8')
        crypt = self.gpg.decrypt(data)
        return crypt.data.decode('utf-8')

    @responses.activate
    def test_create_from_file(self):
        """
        This test checks that the content from a gist created from a file is
        properly encrypted.

        """
        def request_handler(request):
            # Decrypt the content of the request and check that it matches the
            # original content.
            body = json.loads(request.body)
            data = list(body['files'].values())
            text = self.decrypt(data[0]['content'])
            self.assertIn(u'test-content-\u212C', text)

            status = 200
            headers = {}
            body = json.dumps({
                'html_url': 'https://gist.github.com/gists/1'
                })
            return status, headers, body

        responses.add_callback(
                responses.POST,
                'https://api.github.com/gists',
                callback=request_handler,
                content_type='application/json',
                )

        # Create a temporary file and write a test message to it
        with tempfile.NamedTemporaryFile("wb") as fp:
            text = u"test-content-\u212C"
            fp.write(text.encode('utf-8'))
            fp.flush()

            cmd = 'create --encrypt "test-desc" {}'.format(fp.name)
            self.command_response(cmd)

    @responses.activate
    def test_content(self):
        """
        When encrypted content is received, check to make sure that it can be
        properly decrypted.

        """
        def b64encrypt(content):
            return b64encode(self.encrypt(content))

        responses.add(responses.GET, 'https://api.github.com/gists/1',
                body=json.dumps({
                    "files": {
                        "file-A.txt": {
                            "filename": "file-A.txt",
                            "content": b64encrypt(u'test-content-A'),
                            },
                        "file-B.txt": {
                            "filename": "file-B.txt",
                            "content": b64encrypt(u'test-content-\u212C'),
                            },
                        },
                    "description": "test-gist",
                    "public": True,
                    "id": 1,
                    }),
                status=200,
                )

        lines = self.command_response('content 1 --decrypt')

        self.assertIn(u'file-A.txt (decrypted):', lines)
        self.assertIn(u'test-content-A', lines)
        self.assertIn(u'file-B.txt (decrypted):', lines)
        self.assertIn(u'test-content-\u212C', lines)

    def test_gnupg(self):
        """
        Make sure that the basic mechanism put in place for testing the
        encryption used in gist works as expected.

        """
        text = u"this is a message \u212C"
        cypher = self.encrypt(text)
        plain = self.decrypt(cypher)

        self.assertNotEqual(text, cypher)
        self.assertEqual(text, plain)


if __name__ == "__main__":
    unittest.main()
