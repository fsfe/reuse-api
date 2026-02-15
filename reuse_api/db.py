"""Functions responsible managing the filesystem database.

`repo` parameter name originates from here.
It is a string containing two slashes of the following format:

    git_hosting_domain/namespace/project

like

    git.fsfe.org/reuse/api

One can say that it is the HTTP(S) URL without the protocol handle.
The rest of this project should adhere to this rule.
"""

from collections.abc import Callable
from enum import StrEnum
from os import makedirs, mkdir, remove, walk
from os.path import exists, getmtime, isdir, isfile, join, relpath
from shutil import rmtree
from subprocess import CompletedProcess, run
from time import time

from .config import NB_REPOSITORY_BY_PAGINATION as PAGE_SIZE
from .config import REUSE_DB_PATH as DB_ROOT


class Status(StrEnum):
    """Named string enum to ensure string consistency."""

    NULL = "unregistered"
    EMPTY = "uninitialised"
    BAD = "non-compliant"
    OK = "compliant"


# filenames
__HEAD_FILE: str = "HEAD"
__LOG_FILE: str = "log"
__LINT_RVAL: str = "return-value"
__LINT_OUTPUT: str = "lint"
__SPDX_OUTPUT: str = "spdx"
__LOCKFILE: str = ".locked"

UPDATE_TIMEOUT: int = 300  # seconds


# Properties
def __repopath(repo: str) -> str:
    return join(DB_ROOT, repo)


def _repo_file(repo: str, filename: str) -> str:
    return join(__repopath(repo), filename)


def _path_rval(repo: str) -> str:
    return _repo_file(repo, __LINT_RVAL)


def _path_lint(repo: str) -> str:
    return _repo_file(repo, __LINT_OUTPUT)


def _path_head(repo: str) -> str:
    return _repo_file(repo, __HEAD_FILE)


def _path_lock(repo: str) -> str:
    return _repo_file(repo, __LOCKFILE)


# Content functions
def lint_rval(repo: str) -> int:
    """Read the return value of `reuse lint`."""
    with open(_path_rval(repo)) as f:
        return int(f.read())


def is_compliant(repo: str) -> bool:  # pragma: no cover
    """Check if the record is compliant."""
    if not isfile(_path_rval(repo)):
        return False

    return lint_rval(repo) == 0


def lint(repo: str) -> str:  # pragma: no cover
    """Return the `reuse lint` output."""
    with open(_path_lint(repo)) as f:
        return f.read()


def head(repo: str) -> str:  # pragma: no cover
    """Get the HEAD commit hash of a record."""
    with open(_path_head(repo)) as f:
        return f.read()


def name(repo: str) -> str:
    """Cuts out the hosting from the repository repo."""
    return "/".join(repo.split("/")[-2:])


# registration functions
def is_registered(repo: str) -> bool:
    """Check if a repository is registered with us."""
    return isdir(__repopath(repo))


# wrapper for mtime
def check_date(repo: str) -> float:  # pragma: no cover
    """Return the checked date if the last check.

    Will return 0 if the repository is not initialised.
    """
    if not isfile(_path_head(repo)):
        return 0
    return getmtime(_path_head(repo))


def is_older_than(repo: str, age_in_seconds: int) -> bool:
    """Check if the HEAD file is older than age_in_seconds."""
    return time() - check_date(repo) >= age_in_seconds


# wrapper for check_date
def is_initialised(repo: str) -> bool:
    """Return True if HEAD exists."""
    return check_date(repo) != 0


def register(repo: str) -> bool:
    """Register a repository. Return False if project is already registered."""
    if is_registered(repo):
        return False
    # else is not registered
    makedirs(__repopath(repo), exist_ok=True)
    return True


def unregister(repo: str) -> None:
    """Remove a record from our database."""
    rmtree(__repopath(repo), ignore_errors=True)


# Lock functions
def is_lockable(repo: str, timeout: int = UPDATE_TIMEOUT) -> bool:
    """Check if the repo is registered AND if the lock is not there or timed-out."""
    if not is_registered(repo):
        return False
    lockfile = _path_lock(repo)
    # If not locked
    if not exists(lockfile):
        return True
    # If lock timed out
    age: float = time() - getmtime(lockfile)
    return age >= timeout


def __lock(repo: str) -> bool:
    """Lock the file if it can. Reports True if suceeeds."""
    if is_lockable(repo):
        with open(_path_lock(repo), "w"):
            return True
    return False


def __unlock(repo: str) -> None:
    """Remove the lockfile."""
    remove(_repo_file(repo, __LOCKFILE))


# Query functions
def _get_registered_repos(filter_func: Callable) -> list[str]:
    """Return repositories based on a given filter."""
    return [
        relpath(dirpath, DB_ROOT)
        for dirpath, dirnames, filenames in walk(DB_ROOT)
        if dirpath.count("/") - DB_ROOT.count("/") == 2  # noqa: PLR2004
        and filter_func(dirpath, dirnames, filenames)
    ]


def getall() -> list[str]:
    """Return all the repositories that have been registered to the database."""
    return _get_registered_repos(lambda _, __, ___: True)


def compliant() -> list[str]:
    """Return all the compliant repositories."""
    return [r for r in getall() if is_compliant(r)]


def compliant_paged(
    page: int, page_size: int = PAGE_SIZE
) -> list[str]:  # pragma: no cover
    """Pages the compliant repositories sorted by check date."""
    start: int = (page - 1) * page_size
    repos: list[str] = sorted(
        compliant(), reverse=True, key=lambda repo: check_date(repo)
    )
    return repos[start : start + page_size]


def _not_updated() -> list[str]:
    """List the registered repos that have empty database entries."""
    return _get_registered_repos(
        lambda _, dirnames, filenames: not (filenames or dirnames)
    )


def _outdated(age_in_seconds: int = 24 * 60 * 60) -> list[str]:
    """List the updated repos that are outdated."""
    return _get_registered_repos(
        lambda dirpath, _, __: isfile(f"{dirpath}/{__HEAD_FILE}")
        and time() - getmtime(f"{dirpath}/{__HEAD_FILE}") >= age_in_seconds
    )


def get_tasks() -> list[str]:  # pragma: no cover
    """Get the list of the repositories that should be updated."""
    return _not_updated() + _outdated()


def update(repo: str) -> int:
    """Update the database record.

    Also checks for registration
    """
    if not __lock(repo):  # could not lock, another process is doing that
        return 0  # REVIEW: maybe have an enum for this?
    script_name: str = "update-entry.sh"
    proc: CompletedProcess = run(
        [
            "sh",
            "-c",
            f"{script_name} {repo} > {__repopath(repo)}/{__LOG_FILE}",
        ],
        cwd=DB_ROOT,
        timeout=UPDATE_TIMEOUT,
        check=False,  # It can fail
    )
    __unlock(repo)
    return proc.returncode


def reset(repo: str) -> int:  # pragma: no cover
    """Reset the database state of a repository and update it again."""
    unregister(repo)
    register(repo)
    return update(repo)


def drop(really: bool = False) -> None:
    """Delete the database."""
    if not really:
        return
    rmtree(DB_ROOT)
    mkdir(DB_ROOT)


# Frontend functions
def spdx_path(repo: str) -> str:
    """Get the path of the SPDX file.

    Made to be used by flask.send_file.
    """
    return _repo_file(repo, __SPDX_OUTPUT)


def status(repo: str) -> str:  # pragma: no cover
    """Return Status codes based on db contents."""
    if not is_registered(repo):
        return Status.NULL
    if not is_initialised(repo):
        return Status.EMPTY
    if not is_compliant(repo):
        return Status.BAD
    return Status.OK
