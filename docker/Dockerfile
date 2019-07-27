# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2019 Free Software Foundation Europe e.V.

FROM fsfe/reuse:latest

RUN mkdir /project

WORKDIR /project

COPY check-git.sh /bin/

ENTRYPOINT ["check-git.sh"]
