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

from json import dump, loads
from os import rename
from os.path import isfile

from reuse_api.db import register

from .config import FORMS_FILE


# no-cover as it's just stdlib functions
def __move_and_read() -> list:  # pragma: no cover
    """Moves the file and reads it into a list of JSONs"""
    moved: str = FORMS_FILE + "~"
    rename(FORMS_FILE, moved)
    with open(moved) as f:
        return f.read()


def __jsons_to_strings(jsons: list) -> list[str]:
    """Extracts the project names from the details provided by forms"""
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


def mock_add(url: str, forms_file: str = FORMS_FILE) -> None:
    """Mock Forms adding an entry to the file"""  # the file is a list of JSONs

    # if file is not present, create an empty one
    if not isfile(forms_file):
        with open(forms_file, "w") as f:
            f.write("[]")

    # Step 1: Lock the file
    with open(forms_file, "r+") as f:
        # Step 2: Read the contents to a list of dicts
        contents: str = f.read()
        entries: list[dict] = loads(contents) if contents else []

        # Step 3: Append new entry to the list
        new_entry: dict = {
            "timestamp": 0,
            "include_vars": {
                "appid": "reuse-api",
                "project": url,
            },
        }
        entries.append(new_entry)

        # zero the file
        f.seek(0)
        f.truncate()
        # write the new contents
        dump(entries, f)
