import re

def resolve_repository_name(repository_location):
    """
    Resolve repository name from given location
    :param repository_location:
    :return:
    """
    return re.search(r"([^/]*)\.git$", repository_location)[0]


def add_to_gitignore(gitignore_path, ignored_files):
    with open(gitignore_path, 'a+') as f:
        ignored = map(lambda x: x.strip(), f.readlines())

        for ignore in [i for i in ignored_files if i not in ignored]:
            f.writelines([ignore])
