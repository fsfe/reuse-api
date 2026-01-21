import pytest

from json import loads
from os import remove
from os.path import getsize, isfile

from reuse_api import adapter
from reuse_api.db import is_registered

FORMS_CONTENTS: str = """
[
  {
    "timestamp": 1761205404.7610712,
    "from": "",
    "to": [ "" ],
    "subject": "",
    "content": "",
    "reply-to": "",
    "include_vars": {
      "appid": "reuse-api",
      "name": "fkobi",
      "confirm": "fkobi@fsfe.org",
      "project": "github.com/fkobi/date",
      "wantupdates": "False"
    }
  },
  {
    "timestamp": 1763642580.3991778,
    "from": "",
    "to": [ "" ],
    "subject": "",
    "content": "",
    "reply-to": "",
    "include_vars": {
      "appid": "reuse-api",
      "name": "fkobi",
      "confirm": "fkobi@fsfe.org",
      "project": "github.com/fkobi/openrc",
      "wantupdates": "False"
    }
  }
]
"""
FORMS_JSONS = loads(FORMS_CONTENTS)
REPOS: list[str] = ["github.com/fkobi/date", "github.com/fkobi/openrc"]


@pytest.fixture
def tmp_reposfile(tmp_json) -> str:
    """Creates a temporary json file filled with FORMS_CONTENTS"""
    with open(tmp_json, "w") as f:
        f.write(FORMS_CONTENTS)
    return tmp_json


def test_move_and_add(tmp_reposfile) -> None:
    newfile: str = tmp_reposfile + "~"

    assert not isfile(newfile)

    data = adapter.__move_and_read(tmp_reposfile)
    assert data == loads(FORMS_CONTENTS)

    assert not isfile(tmp_reposfile)
    assert isfile(newfile)
    remove(newfile)


def test_extract() -> None:
    jsons: list[dict] = loads(FORMS_CONTENTS)
    assert isinstance(jsons, list)
    assert isinstance(jsons[0], dict)

    repos: list[str] = adapter.__extract_repos(loads(FORMS_CONTENTS))
    assert isinstance(repos, list)
    assert repos == REPOS


def test_register_repos(db_empty) -> None:
    assert not is_registered(REPOS[0])
    assert not is_registered(REPOS[1])

    assert adapter.__register_repos(REPOS)

    assert is_registered(REPOS[0])
    assert is_registered(REPOS[1])

    assert not adapter.__register_repos(REPOS)


def test_move_registrations(db_empty, tmp_reposfile) -> None:
    assert adapter.move_registrations(tmp_reposfile) == REPOS
    assert is_registered(REPOS[0])
    assert is_registered(REPOS[1])


def test_mock_add(tmp_json) -> None:
    remove(tmp_json)
    adapter.mock_add(REPOS[0], forms_file=tmp_json)
    single_size = getsize(tmp_json)
    adapter.mock_add(REPOS[0], forms_file=tmp_json)
    assert single_size < getsize(tmp_json)


def test_full(db_empty, tmp_json) -> None:
    assert not is_registered(REPOS[0])
    adapter.mock_add(REPOS[0], forms_file=tmp_json)
    assert adapter.__register_repos(REPOS)
    assert is_registered(REPOS[1])
