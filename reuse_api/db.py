"""This file hosts the functions responsible managing the filesystem database."""

from collections.abc import Callable
from os import makedirs, mkdir, remove, walk
from os.path import exists, getmtime, isdir, isfile, join, relpath
from shutil import rmtree
from subprocess import CompletedProcess, run
from time import time

from .config import REUSE_DB_PATH as DB_ROOT
from .config import NB_REPOSITORY_BY_PAGINATION as PAGE_SIZE


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


def _path_spdx(repo: str) -> str:
    return _repo_file(repo, __SPDX_OUTPUT)


def _path_head(repo: str) -> str:
    return _repo_file(repo, __HEAD_FILE)


def _path_lock(repo: str) -> str:
    return _repo_file(repo, __LOCKFILE)


# Content functions
def lint_rval(repo: str) -> int:
    with open(_path_rval(repo)) as f:
        return int(f.read())


def lint_isok(repo: str) -> bool:
    return lint_rval(repo) == 0


def lint(repo: str) -> str:  # pragma: no cover
    """Returns the `reuse lint` output"""
    with open(_path_lint(repo)) as f:
        return f.read()


def spdx(repo: str) -> str:  # pragma: no cover
    """Returns the `reuse spdx` output"""
    with open(_path_spdx(repo)) as f:
        return f.read()


# registration functions
def is_registered(repo: str) -> bool:
    return isdir(__repopath(repo))


# wrapper for mtime
def check_date(repo: str) -> float:  # pragma: no cover
    """Returns the checked date if the last check"""
    return getmtime(_path_head(repo))


def register(repo: str) -> bool:
    """Register a repository. Returns False if project is already registered."""
    if is_registered(repo):
        return False
    # else is not registered
    makedirs(__repopath(repo), exist_ok=True)
    return True


def unregister(repo: str) -> None:
    rmtree(__repopath(repo), ignore_errors=True)


# Lock functions
def is_lockable(repo: str, timeout: int = UPDATE_TIMEOUT) -> bool:
    """Checks if the repo is registered AND
    if the lock is not there or timed-out."""
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
    """Locks the file if it can. Reports True if suceeeds."""
    if is_lockable(repo):
        with open(_path_lock(repo), "w"):
            return True
    return False


def __unlock(repo: str) -> None:
    """Removes the lockfile"""
    remove(_repo_file(repo, __LOCKFILE))


# Query functions
def _get_registered_repos(filter_func: Callable) -> list[str]:
    """Helper function to return repositories based on a given filter."""
    return [
        relpath(dirpath, DB_ROOT)
        for dirpath, dirnames, filenames in walk(DB_ROOT)
        if dirpath.count("/") - DB_ROOT.count("/") == 2
        and filter_func(dirpath, dirnames, filenames)
    ]


def getall() -> list[str]:
    """Returns all the repositories that have been registered to the database."""
    return _get_registered_repos(lambda _, __, ___: True)


def compliant() -> list[str]:
    """Returns all the compliant repositories"""
    return [r for r in getall() if lint_isok(r)]


def compliant_paged(page: int, page_size: int = PAGE_SIZE) -> list[str]:
    """Pages the compliant repositories sorted by check date"""
    start: int = (page - 1) * page_size

    repo_with_mtime: list[tuple[str, float]] = [
        (repo, check_date(repo)) for repo in compliant()
    ]
    mtime_sorted: list[tuple[str, float]] = sorted(
        repo_with_mtime, key=lambda x: x[1], reverse=True
    )

    return mtime_sorted[start : start + page_size][0][:1]  # pick only the first column


def _not_updated() -> list[str]:
    """Lists the registered repos that have empty database entries."""
    return _get_registered_repos(
        lambda _, dirnames, filenames: not (filenames or dirnames)
    )


def _outdated(age_in_seconds: int = 24 * 60 * 60) -> list[str]:
    """Lists the updated repos that are outdated."""
    return _get_registered_repos(
        lambda dirpath, _, __: isfile(f"{dirpath}/{__HEAD_FILE}")
        and time() - getmtime(f"{dirpath}/{__HEAD_FILE}") >= age_in_seconds
    )


def get_tasks() -> list[str]:  # pragma: no cover
    """Returns the list of the repositories that should be updated."""
    return _not_updated() + _outdated()


def update(repo: str) -> int:
    # Also checks for registration
    if not __lock(repo):  # could not lock, another process is doing that
        return 0  # REVIEW: maybe have an enum for this?
    script_name: str = "update-entry.sh"
    print("LOG: Running")
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
    print("LOG: done")
    __unlock(repo)
    return proc.returncode


def drop(really: bool = False) -> None:
    if not really:
        return
    rmtree(DB_ROOT)
    mkdir(DB_ROOT)
