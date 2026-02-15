<!--
SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# REUSE API

[![Build Status](https://drone.fsfe.org/api/badges/reuse/api/status.svg)](https://drone.fsfe.org/reuse/api)
[![REUSE compliant](https://api.reuse.software/badge/git.fsfe.org/reuse/api)](https://api.reuse.software/info/git.fsfe.org/reuse/api)

The REUSE API checks repositories for their compliance with the [best
practices](https://reuse.software). It basically runs the [helper
tool](https://git.fsfe.org/reuse/tool) for the default branch of a
project.

REUSE offers [many tools and methods](https://reuse.software/dev/) to
support developers in making their licensing more clear and simple. This
API is an additional component and enables other users to see a
project's REUSE status transparently.

This repository contains the web part for all user interaction. The
parts needed for the external server performing the checks are hosted in
the [api-worker](https://git.fsfe.org/reuse/api-worker) repository.


## Features

* Users can register any public Git repository with this API.
* The API runs the linter on each registered project.
* Re-check projects if they have been updated (new commit).
* Informative information page for each registered project.
* Offer a live badge indicating the REUSE compliance status.
* Offer a JSON for parsing the current REUSE status.


## Background

Copyright and licensing is difficult, especially when reusing software
from different projects that are released under various different
licenses. REUSE was started by the Free Software Foundation Europe
(FSFE) to provide a set of recommendations to make licensing your Free
Software projects easier. Not only do these recommendations make it
easier for you to declare the licenses under which your works are
released, but they also make it easier for a computer to understand how
your project is licensed.

As a short summary, the recommendations are threefold:

1. Choose and provide licenses
2. Add copyright and licensing information to each file
3. Confirm REUSE compliance

You are recommended to read the
[recommendations](https://reuse.software) in full for more details.


## Maintainers

* Max Mehl ([contact](https://fsfe.org/about/mehl))


## Contribute

Any pull requests or suggestions are welcome at
https://git.fsfe.org/reuse/api or via e-mail to one of the maintainers.
General inquiries can be sent to [the REUSE mailing
list](https://lists.fsfe.org/mailman/listinfo/reuse).

Information on how to develop and hack around with this project can be
found in the file [doc/hack.md](./doc/hack.md).
