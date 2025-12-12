"""
This file hosts the code responsible for moving the registration
data from FORMS_FILE to the project's database.

It is split into a number of smaller, unit-testable functions that
can be easily unit-tested.

It assumes that the file is a list of JSONs of the following structure:
```json5
"timestamp": <float>,
"from": "",
"to": [ "" ],
"subject": "",
"content": "",
"reply-to": "",
"include_vars": {
  "appid": "reuse-api",
  "name": "<name>",
  "confirm": "<email>",
  "project": "<repo-string>", // ex. "github.com/foo/bar"
  "wantupdates": "<bool>"
}
```
"""

from reuse_api.db import is_registered, register

from .config import FORMS_FILE

from json import loads
from os import rename


# no-cover as it's just stdlib functions
def __move_and_read() -> list:  # pragma: no cover
    """Moves the file and reads it into a list of JSONs"""
    moved: str = FORMS_FILE + "~"
    rename(FORMS_FILE, moved)
    with open(moved) as f:
        return f.read()


def __jsons_to_strings(jsons: list) -> list[str]:
    return [r["include_vars"]["project"] for r in jsons]


def __register_repos(urls: list[str]) -> bool:
    """Registeres all the urls as repositories.
    Returns True if none of them were registered"""
    all_good: bool = True
    for repo in urls:
        if not register(repo):
            all_good = False
    return all_good


# no-cover as we assume that if the functions work this will also do
def move_registrations() -> list[str]:  # pragma: no cover
    """Adds `~` to the filename, extracts the URLs and registers them.
    If all of the registrations are new returns True."""
    repos: list[str] = __contents_to_strings(__move_and_read())
    __register_repos(repos)
    return repos
