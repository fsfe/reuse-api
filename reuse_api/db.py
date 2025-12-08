"""This file hosts the functions responsible managing the filesystem database."""

from os import makedirs, mkdir, remove
from os.path import exists, getmtime, isdir, join
from shutil import rmtree
from subprocess import CompletedProcess, run
from time import time

from .config import REUSE_DB_PATH as DB_ROOT


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
def register(repo: str) -> None:
    makedirs(__repopath(repo), exist_ok=True)


def unregister(repo: str) -> None:
    rmtree(__repopath(repo), ignore_errors=True)


def is_registered(repo: str) -> bool:
    return isdir(__repopath(repo))


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


# Update
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
