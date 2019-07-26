#!/bin/sh

GIT=$1
OPTIONS=$2

# Test if remote repository is valid
if git ls-remote "${GIT}" > /dev/null; then
  echo "${GIT} is a valid git repository"
else
  echo "${GIT} is not a valid git repository"
  exit 42
fi

# Cloning git repo
git clone "${GIT}" /project

# Running reuse lint with optional parameters
printf "\nRunning REUSE check:\n\n"
reuse lint "${OPTIONS}"
