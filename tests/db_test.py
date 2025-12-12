# ruff: noqa: ARG001
# function argumens are used to implement fixture dependencies
from os.path import isfile

import pytest

from .conftest import TEST_REPO
from reuse_api import db


def test_registration(db_empty) -> None:
    my_repo: str = "beka.ovh/fkobi/emacs-config"
    # test not registered
    assert not db.is_registered(my_repo)
    # test registration
    db.register(my_repo)
    assert db.is_registered(my_repo)
    # test unregistration
    db.unregister(my_repo)
    assert not db.is_registered(my_repo)


def test_lock(db_empty) -> None:
    # Unregistered is not lockable
    assert not db.is_lockable(TEST_REPO)

    # Registered success
    db.register(TEST_REPO)
    assert db.__lock(TEST_REPO)

    # Locked is not lockable
    assert not db.is_lockable(TEST_REPO)

    # Timed-out lock is lockable
    assert db.is_lockable(TEST_REPO, timeout=-1)

    # Relock success
    db.__unlock(TEST_REPO)
    assert db.__lock(TEST_REPO)


def test_update_locked(db_registered) -> None:
    assert db.__lock(TEST_REPO)
    assert db.update(TEST_REPO) == 0  # NOTE: maybe it should be enumed


def test_all_files_present(db_updated) -> None:
    assert isfile(db._path_rval(TEST_REPO))
    assert isfile(db._path_lint(TEST_REPO))
    assert isfile(db._path_spdx(TEST_REPO))
    assert isfile(db._path_head(TEST_REPO))


def test_isok(db_updated) -> None:
    assert db.lint_isok(TEST_REPO)


def test_drop(db_registered) -> None:
    assert db.is_registered(TEST_REPO)
    db.drop()
    assert db.is_registered(TEST_REPO)
    db.drop(really=True)
    assert not db.is_registered(TEST_REPO)
