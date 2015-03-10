#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import contextlib
import imp
import shlex
import sys
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
setattr(gist, 'cli', imp.load_source('cli', '../bin/gist'))


@contextlib.contextmanager
def redirect_stdout(buf):
    original = sys.stdout
    sys.stdout = buf
    yield
    sys.stdout = original



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

        gists = gist.GistAPI(token='foo').list()

        gistA = gists[0]
        gistB = gists[1]

        self.assertEqual(gistA.id, 1)
        self.assertEqual(gistA.desc, 'test-desc-A')
        self.assertTrue(gistA.public)

        self.assertEqual(gistB.id, 2)
        self.assertEqual(gistB.desc, 'test-desc-\u212C')
        self.assertFalse(gistB.public)

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

        content = gist.GistAPI(token='foo').content('1')

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

        gist.GistAPI(token='foo').create(desc, files, public)


class TestGistCLI(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()
        self.config.add_section('gist')
        self.config.set('gist', 'token', 'foo')

    def command_response(self, cmd):
        buf = StringIO()
        with redirect_stdout(buf):
            gist.cli.main(argv=shlex.split(cmd), config=self.config)

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


if __name__ == "__main__":
    unittest.main()
