import tempfile
from os import mkdir
from os.path import join, exists

from git import Repo, Git


class Templates(object):
    REPOSITORY = 'git@github.com:ThreadsStylingLtd/templates.git'

    def __init__(self, version):
        self.version = version
        self.destination = join(tempfile.gettempdir(), "stylist-templates")
        self._init_repository()

    def _init_repository(self):
        if not exists(self.destination):
            mkdir(self.destination)
            Git().clone(Templates.REPOSITORY, self.destination)

        repo = Repo(self.destination)
        repo.git.checkout(self.version)
        repo.remote("origin").pull()
