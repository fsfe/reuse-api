import pytest
from json import loads

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


def test_project_extraction() -> None:
    assert REPOS == adapter.__jsons_to_strings(FORMS_JSONS)


def test_register_repos(db_empty) -> None:
    assert not is_registered(REPOS[0])
    assert not is_registered(REPOS[1])

    assert adapter.__register_repos(REPOS)

    assert is_registered(REPOS[0])
    assert is_registered(REPOS[1])

    assert not adapter.__register_repos(REPOS)
