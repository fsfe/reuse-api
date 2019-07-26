#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2019 Free Software Foundation Europe e.V.

GIT=$1
OPTIONS=$2

# Test if remote repository is valid
if ! git ls-remote "${GIT}" > /dev/null; then
  echo "${GIT} is not a valid git repository"
  exit 42
fi

# Cloning git repo
git clone --depth 1 "${GIT}" /project

# Running reuse lint with optional parameters
printf "\nRunning REUSE check:\n\n"
reuse lint "${OPTIONS}"
