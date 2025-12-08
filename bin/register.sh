#!/bin/sh -eu
# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This script takes the repos.json file ($1), extracts the URLs
# of the registered projects and registers them in the database
# ($2) which basically means creating folders.

REPOS_FILE=$1
DB_ROOT=$2
WORKFILE=$REPOS_FILE.work

test -w "$REPOS_FILE"
test -d "$DB_ROOT"

mv "$REPOS_FILE" "$WORKFILE"

# Extract project and set the provider to lowercase
REPOS_LIST=$(jq -r '.[].include_vars.project' "$WORKFILE" | awk -F'/' '{printf "%s/%s/%s\n", tolower($1), $2, $3}')

for repo in $REPOS_LIST; do
	mkdir -vp "$DB_ROOT/$repo"
done

rm "$WORKFILE"
