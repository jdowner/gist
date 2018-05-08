import base64
import collections
import contextlib
import simplejson as json
import os
import re
import requests
import shutil
import tarfile
import tempfile

__version__ = '0.6.1'

requests.packages.urllib3.disable_warnings()


@contextlib.contextmanager
def pushd(path):
    original = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(original)


class GistInfo(collections.namedtuple('GistInfo', 'id public desc')):
    pass


class authenticate(object):
    """
    The class is used as a decorator to handle token authentication with
    github.
    """

    def __init__(self, func, method='GET'):
        """Create an authenticate object

        Arguments:
            func: a function to decorate
            method: the method of the request to construct

        """
        self.func = func
        self.owner = None
        self.instance = None
        self.headers = {
                'Accept-Encoding': 'identity, deflate, compress, gzip',
                'User-Agent': 'python-requests/1.2.0',
                'Accept': 'application/vnd.github.v3.base64',
                }
        self.method = method

    @classmethod
    def get(cls, func):
        """Create an authenticate object with a GET method

        Arguments:
            func: a function to decorate

        """
        return cls(func, method='GET')

    @classmethod
    def post(cls, func):
        """Create an authenticate object with a POST method

        Arguments:
            func: a function to decorate

        """
        return cls(func, method='POST')

    @classmethod
    def patch(cls, func):
        """Create an authenticate object with a PATCH method

        Arguments:
            func: a function to decorate

        """
        return cls(func, method='PATCH')

    @classmethod
    def delete(cls, func):
        """Create an authenticate object with a DELETE method

        Arguments:
            func: a function to decorate

        """
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
            request = requests.Request(
                    self.method,
                    url,
                    headers=self.headers,
                    params=params,
                    )
            return self.func(self.instance, request, *args, **kwargs)
        finally:
            self.instance = None
            self.owner = None


class GistAPI(object):
    """
    This class defines the interface to github.
    """

    def __init__(self, token, editor=None):
        """Create a GistAPI object

        Arguments:
            token: an authentication token
            editor: path to the editor to use when editing a gist

        """
        self.token = token
        self.editor = editor
        self.session = requests.Session()

    def send(self, request, stem=None):
        """Prepare and send a request

        Arguments:
            request: a Request object that is not yet prepared
            stem: a path to append to the root URL

        Returns:
            The response to the request

        """
        if stem is not None:
            request.url = request.url + "/" + stem.lstrip("/")

        prepped = self.session.prepare_request(request)
        settings = self.session.merge_environment_settings(url=prepped.url,
                                                           proxies={},
                                                           stream=None,
                                                           verify=None,
                                                           cert=None)

        return self.session.send(prepped, **settings)

    def list(self):
        """Returns a list of the users gists as GistInfo objects

        Returns:
            a list of GistInfo objects

        """
        # Define the basic request. The per_page parameter is set to 100, which
        # is the maximum github allows. If the user has more than one page of
        # gists, this request object will be modified to retrieve each
        # successive page of gists.
        request = requests.Request(
                'GET',
                'https://api.github.com/gists',
                headers={
                    'Accept-Encoding': 'identity, deflate, compress, gzip',
                    'User-Agent': 'python-requests/1.2.0',
                    'Accept': 'application/vnd.github.v3.base64',
                    },
                params={
                    'access_token': self.token,
                    'per_page': 100,
                    },
                )

        # Github provides a 'link' header that contains information to
        # navigate through a users page of gists. This regex is used to
        # extract the URLs contained in this header, and to find the next page
        # of gists.
        pattern = re.compile(r'<([^>]*)>; rel="([^"]*)"')

        gists = []
        while True:

            # Retrieve the next page of gists
            try:
                response = self.send(request).json()

            except Exception:
                break

            # Extract the list of gists
            for gist in response:
                try:
                    gists.append(
                            GistInfo(
                                gist['id'],
                                gist['public'],
                                gist['description'],
                                )
                            )

                except KeyError:
                    continue

            try:
                link = response.headers['link']

                # Search for the next page of gist. If a 'next' page is found,
                # the URL is set to this new page and the iteration continues.
                # If there is no next page, return the list of gists.
                for result in pattern.finditer(link):
                    url = result.group(1)
                    rel = result.group(2)
                    if rel == 'next':
                        request.url = url
                        break
                else:
                    return gists

            except Exception:
                break

        return gists

    @authenticate.post
    def create(self, request, desc, files, public=False):
        """Creates a gist

        Arguments:
            request: an initial request object
            desc:    the gist description
            files:   a list of files to add to the gist
            public:  a flag to indicate whether the gist is public or not

        Returns:
            The URL to the newly created gist.

        """
        request.data = json.dumps({
                "description": desc,
                "public": public,
                "files": files,
                })
        return self.send(request).json()['html_url']

    @authenticate.delete
    def delete(self, request, id):
        """Deletes a gist

        Arguments:
            request: an initial request object
            id:      the gist identifier

        """
        self.send(request, id)

    @authenticate.get
    def info(self, request, id):
        """Returns info about a given gist

        Arguments:
            request: an initial request object
            id:      the gist identifier

        Returns:
            A dict containing the gist info

        """
        return self.send(request, id).json()

    @authenticate.get
    def files(self, request, id):
        """Returns a list of files in the gist

        Arguments:
            request: an initial request object
            id:      the gist identifier

        Returns:
            A list of the files

        """
        gist = self.send(request, id).json()
        return gist['files']

    @authenticate.get
    def content(self, request, id):
        """Returns the content of the gist

        Arguments:
            request: an initial request object
            id:      the gist identifier

        Returns:
            A dict containing the contents of each file in the gist

        """
        gist = self.send(request, id).json()

        def convert(data):
            return base64.b64decode(data).decode('utf-8')

        content = {}
        for name, data in gist['files'].items():
            content[name] = convert(data['content'])

        return content

    @authenticate.get
    def archive(self, request, id):
        """Create an archive of a gist

        The files in the gist are downloaded and added to a compressed archive
        (tarball). If the ID of the gist was c78d925546e964b4b1df, the
        resulting archive would be,

            c78d925546e964b4b1df.tar.gz

        The archive is created in the directory where the command is invoked.

        Arguments:
            request: an initial request object
            id:      the gist identifier

        """
        gist = self.send(request, id).json()

        with tarfile.open('{}.tar.gz'.format(id), mode='w:gz') as archive:
            for name, data in gist['files'].items():
                with tempfile.NamedTemporaryFile('w+') as fp:
                    fp.write(data['content'])
                    fp.flush()
                    archive.add(fp.name, arcname=name)

    @authenticate.get
    def edit(self, request, id):
        """Edit a gist

        The files in the gist a cloned to a temporary directory and passed to
        the default editor (defined by the EDITOR environmental variable). When
        the user exits the editor, they will be provided with a prompt to
        commit the changes, which will then be pushed to the remote.

        Arguments:
            request: an initial request object
            id:      the gist identifier

        """
        with pushd(tempfile.gettempdir()):
            try:
                self.clone(id)
                with pushd(id):
                    files = [f for f in os.listdir('.') if os.path.isfile(f)]
                    quoted = ['"{}"'.format(f) for f in files]
                    os.system("{} {}".format(self.editor, ' '.join(quoted)))
                    os.system('git commit -av && git push')

            finally:
                shutil.rmtree(id)

    @authenticate.post
    def fork(self, request, id):
        """Fork a gist

        Forks an existing gist.

        Arguments:
            request: an initial request object
            id:      the gist identifier

        """
        return self.send(request, '{}/forks'.format(id))

    @authenticate.patch
    def description(self, request, id, description):
        """Updates the description of a gist

        Arguments:
            request:     an initial request object
            id:          the id of the gist we want to edit the description for
            description: the new description

        """
        request.data = json.dumps({
            "description": description
        })
        return self.send(request, id).json()['html_url']

    def clone(self, id, name=None):
        """Clone a gist

        Arguments:
            id:   the gist identifier
            name: the name to give the cloned repo

        """
        url = 'git@gist.github.com:/{}'.format(id)

        if name is None:
            os.system('git clone {}'.format(url))
        else:
            os.system('git clone {} {}'.format(url, name))
