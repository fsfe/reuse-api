# ruff: noqa: ARG001
# function argumens are used to implement fixture dependencies
from os.path import isfile

import pytest

from .conftest import TEST_REPO
from reuse_api import db


def test_name() -> None:
    url: str = "hosting/user/repo"
    assert db.name(url) == "user/repo"


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


def test_getall(db_empty) -> None:
    assert not db.getall()
    db.register(TEST_REPO)
    assert db.getall() == [TEST_REPO]


def test_outdated(db_registered) -> None:
    assert not db._outdated()  # Not registered so not outdated
    db.update(TEST_REPO)
    assert not db._outdated()  # Freshly registered
    assert db._outdated(age_in_seconds=-1) == [TEST_REPO]


def test_update_locked(db_registered) -> None:
    assert db.__lock(TEST_REPO)
    assert db.update(TEST_REPO) == 0  # NOTE: maybe it should be enumed


def test_check_date(db_updated) -> None:
    repo: str = "a/b/c"
    db.register(repo)
    with open(db._path_head(repo), "w"):
        pass
    assert db.check_date(repo) > db.check_date(TEST_REPO)


def test_all_files_present(db_updated) -> None:
    assert isfile(db._path_rval(TEST_REPO))
    assert isfile(db._path_lint(TEST_REPO))
    assert isfile(db._path_spdx(TEST_REPO))
    assert isfile(db._path_head(TEST_REPO))


def test_compliance(db_updated) -> None:
    """Assumes that the project itself is compliant"""
    assert db.is_compliant(TEST_REPO)
    assert db.compliant() == [TEST_REPO]


def test_not_updated(db_registered) -> None:
    assert db._not_updated() == [TEST_REPO]
    assert db.__lock(TEST_REPO)
    assert db._not_updated() == []


def test_drop(db_registered) -> None:
    assert db.is_registered(TEST_REPO)
    db.drop()
    assert db.is_registered(TEST_REPO)
    db.drop(really=True)
    assert not db.is_registered(TEST_REPO)
