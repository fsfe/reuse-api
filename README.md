<!--
  SPDX-License-Identifier: GPL-3.0-or-later
  Copyright © 2019 Free Software Foundation Europe e.V.
-->

# REUSE API

These are the first elements for an API people can use to check their repo's REUSE compliance.

The idea is that users provide their repo's Git address and optional parameters (e.g. future submodule options), and we do all the cloning, linting, and provision of icons.

Having an API would also be important for inclusion in other services like shields.io or source forges.

## Installation

Currently, the Docker container is the heart. It is based on fsfe/reuse and contains the simple script `check-git.sh` in this repository.

To build the image, run `docker build -t reuse-api .`

## Usage

Running the check is fairly simple:

```text
$ docker run --rm reuse-api https://git.fsfe.org/reuse/tool
https://git.fsfe.org/reuse/tool is a valid git repository
Cloning into '/project'...
remote: Counting objects: 3191, done.
remote: Compressing objects: 100% (1539/1539), done.
remote: Total 3191 (delta 1793), reused 2323 (delta 1241)
Receiving objects: 100% (3191/3191), 884.51 KiB | 1.41 MiB/s, done.
Resolving deltas: 100% (1793/1793), done.

Running REUSE check:

SUMMARY

Bad licenses: 0
Missing licenses: 0
Unused licenses: 0
Used licenses: Apache-2.0, CC-BY-SA-4.0, CC0-1.0, GPL-3.0-or-later
Read errors: 0
Files with copyright information: 51 / 51
Files with license information: 51 / 51

Congratulations! Your project is REUSE compliant :-)
```

The exit codes of this command can be evaluated in a later stage, so that a web service could decide which badge to display.

## License

GNU GPL 3.0 or any later version (GPL-3.0-or-later)
