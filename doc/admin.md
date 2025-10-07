<!--
SPDX-FileCopyrightText: 2023 DB Systel GmbH

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Typical admin operations

There are some functions that admins of the REUSE API can execute. Instead of
direct database operations, these are (usually) executed via POST requests.

Typically, these require a secret "admin key". This is set as an environment
variable by the Drone CI's secret store. In the examples below, we assume the
`admin_key` is `4dm1nk3y`.

## List all registered projects

Get a JSON array of all projects that are handled by the REUSE API.

```sh
curl -X POST \
  -F "admin_key=4dm1nk3y" \
  https://api.reuse.software/admin/analytics/all_projects.json
```

Exemplary output:

```json
[
  {
    "hash": "b7996318548cf0649952a497e38d1c7bc06d66b6",
    "last_access": "Wed, 10 May 2023 09:07:04 GMT",
    "lint_code": 0,
    "status": "compliant",
    "url": "github.com/org1/repo1"
  },
  {
    "hash": "c753c9affa3d1ce8259ffeb2ee0886b8e921ba97",
    "last_access": "Wed, 26 Feb 2020 19:52:05 GMT",
    "lint_code": 1,
    "status": "non-compliant",
    "url": "github.com/user1/repo2"
  }
]
```

You can also list all projects filtered by a certain status:

```sh
curl -X POST \
  -F "admin_key=4dm1nk3y" \
  -F "status=non_compliant" \
  https://api.reuse.software/admin/analytics/projects_by_status.json`
```


## Force re-scan of a project

It may be helpful to trigger a complete re-scan of a project, e.g. if an earlier
scan failed due to a technical issue.

Command: `curl -X POST -F "admin_key=4dm1nk3y" https://api.reuse.software/admin/reset/git.fsfe.org/reuse/api`

Exemplary output: `Repository git.fsfe.org/reuse/api has been scheduled for re-check`


## Force re-scan of all projects

This is a combination of two admin commands solved with a very naive local loop,
executed in `bash`. Note that this will take at least a two-digit amount of
minutes.

Command:

```sh
# Set admin key as local env
ADMIN_KEY=4dm1nk3y

# Get all repos, write their URLs to file
curl -X POST -F "admin_key=${ADMIN_KEY}" https://api.reuse.software/admin/analytics/all_projects.json \
  | jq -r '.[].url' > repos.txt

# Loop reset for all repos
while read line; do
  curl -X POST -F "admin_key=${ADMIN_KEY}" "https://api.reuse.software/admin/reset/$line"
done < repos.txt

# Delete temporary repo file
rm repos.txt
```

Exemplary output:

```
Repository github.com/org1/repo1 has been scheduled for re-check
Repository github.com/user1/repo2 has been scheduled for re-check
```
