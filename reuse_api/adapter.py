"""Code responsible for moving the registration data from FORMS_FILE to the database.

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


def __move_and_read(forms_file: str) -> list[dict]:
    """Move the file and read it into a list of JSONs."""
    moved: str = forms_file + "~"
    rename(forms_file, moved)
    with open(moved) as f:
        return loads(f.read())


def __extract_repos(jsons: list[dict]) -> list[str]:
    """Extract the project names from the list of JSONs."""
    return [r["include_vars"]["project"] for r in jsons]


def __register_repos(repos: list[str]) -> bool:
    """Registeres all the repos as repositories.

    Returns True if none of them were registered.
    """
    all_good: bool = True
    for repo in repos:
        if not register(repo):
            all_good = False
    return all_good


def move_registrations(forms_file: str) -> list[str]:
    """Add `~` to the filename, extract the repos & register them."""
    repos: list[str] = __extract_repos(__move_and_read(forms_file))
    __register_repos(repos)
    return repos


def mock_add(repo: str, forms_file: str = FORMS_FILE) -> None:
    """Mock Forms adding an entry to the file."""  # the file is a list of JSONs
    # if file is not present, create an empty one
    if not isfile(forms_file):
        with open(forms_file, "w") as f:
            f.write("[]")

    # Step 1: Lock the file
    with open(forms_file, "r+") as f:
        # Step 2: Read the contents to a list of dicts
        contents: str = f.read()
        entries: list[dict] = list(loads(contents)) if contents else []

        # Step 3: Append new entry to the list
        new_entry: dict = {
            "timestamp": 0,
            "include_vars": {
                "appid": "reuse-api",
                "project": repo,
            },
        }
        entries.append(new_entry)

        # zero the file
        f.seek(0)
        f.truncate()
        # write the new contents
        dump(entries, f)
