#!/usr/bin/env python

import argparse
import fcntl
import json
import os
import requests
import struct
import sys
import tarfile
import tempfile
import termios

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


def terminal_width():
    """Returns the terminal width

    Tries to determine the width of the terminal. If there is no terminal, then
    None is returned instead.

    """
    try:
        h, w, hp, wp = struct.unpack('HHHH',
            fcntl.ioctl(0, termios.TIOCGWINSZ,
            struct.pack('HHHH', 0, 0, 0, 0)))
        return w
    except IOError:
        pass


def elide(txt, width=terminal_width()):
    """Elide the provided string

    The string is elided to the specified width, which defaults to the width of
    the terminal.

    """
    try:
        if len(txt) > width:
            return txt[:width - 3] + '...'
    except Exception:
        pass
    return txt


class authenticate(object):
    """
    The class is used as a decorator to handle token authentication with github.
    """

    def __init__(self, func, method='GET'):
        self.func = func
        self.owner = None
        self.instance = None
        self.headers = {
                'Accept-Encoding': 'identity, deflate, compress, gzip',
                'User-Agent': 'python-requests/1.2.0',
                'Accept': '*/*',
                }
        self.method = method

    @classmethod
    def get(cls, func):
        return cls(func, method='GET')

    @classmethod
    def post(cls, func):
        return cls(func, method='POST')

    @classmethod
    def delete(cls, func):
        return cls(func, method='DELETE')

    def __get__(self, instance, owner):
        """Returns the __call__ method

        This method is part of the data descriptor interface. It returns the
        __call__ method, which wraps the original function.

        """
        self.instance = instance
        self.owner = owner
        return self.__call__

    def __call__(self, *args, **kwargs):
        """Wraps the original function and provides an initial request.

        The request object is created with the instance token as a query
        parameter, and specifies the required headers.

        """
        try:
            url = 'https://api.github.com/gists'
            params = {'access_token': self.instance.token}
            request = requests.Request(self.method, url, headers=self.headers, params=params)
            return self.func(self.instance, request, *args, **kwargs)
        finally:
            self.instance = None
            self.owner = None


class GistAPI(object):
    """
    This class defines the interface to github.
    """

    def __init__(self, token):
        self.token = token

    def send(self, request, stem=None):
        if stem is not None:
            request.url = os.path.join(request.url, stem)
        return requests.Session().send(request.prepare())

    @authenticate.get
    def list(self, request):
        gists = self.send(request).json()
        for gist in gists:
            desc = gist['description']
            public = '+' if gist['public'] else '-'
            line = '{} {} {}'.format(gist['id'], public, desc)
            print(elide(line))

    @authenticate.post
    def create(self, request, desc, files, public=False):
        request.data = json.dumps({
                "description": desc,
                "public": public,
                "files": files,
                })
        print(self.send(request).json()['url'])

    @authenticate.delete
    def delete(self, request, id):
        self.send(request, id)

    @authenticate.get
    def clone(self, request, id, name=''):
        response = self.send(request, id).json()
        os.system('git clone {} {}'.format(response['git_pull_url'], name))

    @authenticate.get
    def info(self, request, id):
        gist = self.send(request, id).json()
        print(json.dumps(gist, indent=2))

    @authenticate.get
    def files(self, request, id):
        gist = self.send(request, id).json()
        for name in gist['files']:
            print(name)

    @authenticate.get
    def content(self, request, id):
        gist = self.send(request, id).json()
        for name, data in gist['files'].items():
            print('{}:\n'.format(name))
            for line in data['content'].splitlines():
                print(line)
            print
            print

    @authenticate.get
    def archive(self, request, id):
        gist = self.send(request, id).json()

        with tarfile.open('{}.tar.gz'.format(id), mode='w:gz') as archive:
            for name, data in gist['files'].items():
                with tempfile.NamedTemporaryFile() as fp:
                    fp.write(data['content'])
                    fp.seek(0)
                    archive.add(fp.name, arcname=name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--info', action='store_true')
    parser.add_argument('--clone', action='store_true')
    parser.add_argument('--content', action='store_true')
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--delete', action='store_true')
    parser.add_argument('--files', action='store_true')
    parser.add_argument('--archive', action='store_true')
    parser.add_argument('--public', dest='public', action='store_true')
    parser.add_argument('--private', dest='public', action='store_false')
    parser.add_argument('-i', '--id')
    parser.add_argument('-n', '--name', default='')
    parser.add_argument('-d', '--desc', nargs='+')
    parser.add_argument('-f', '--filenames', nargs='+')
    parser.add_argument('-c', '--config', default=os.path.expanduser('~/.gist'))

    args = parser.parse_args()

    config = configparser.ConfigParser()
    with open(args.config) as fp:
        config.readfp(fp)

    gist = GistAPI(token=config.get('gist', 'token'))

    if args.list:
        gist.list()
        sys.exit(0)

    if args.info:
        gist.info(args.id)
        sys.exit(0)

    if args.clone:
        gist.clone(args.id, args.name)
        sys.exit(0)

    if args.content:
        gist.content(args.id)
        sys.exit(0)

    if args.files:
        gist.files(args.id)
        sys.exit(0)

    if args.archive:
        gist.archive(args.id)
        sys.exit(0)

    if args.delete:
        gist.delete(args.id)
        sys.exit(0)

    if args.create:
        if sys.stdin.isatty():
            description = ' '.join(args.desc)
            files = {f: {'content': open(f).read()} for f in args.filenames}
            gist.create(description, files, args.public)
        else:
            content = sys.stdin.read()
            description = ' '.join(args.desc)
            public = args.public
            files = {
                    'file1.txt': {
                        'content': content,
                        }
                    }
            gist.create(description, files, public)
        sys.exit(0)

    sys.exit(1)
