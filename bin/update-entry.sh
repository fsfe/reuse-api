#!/bin/sh -eu
# SPDX-FileCopyrightText: 2026 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# we want to use `local`
# shellcheck disable=3043

# NOTE: this script assumes tht the repository is registered & online

REUSE_TMP="/tmp/reuse-api"

# per-repo variables
URL="$1" # no git/ssh for now

URL_REMOTE="https://$URL"
TMP_REPO="$REUSE_TMP/$URL"


# Updates head file and returns 1 if it was outdated
head_was_latest() {
    local HEAD="${URL}/HEAD"
    echo "HEAD checking..."
    git ls-remote "${URL_REMOTE}" HEAD | cut -f 1 | tr -d '\n' > "$HEAD".new

    # this also works with no file
    if ! cmp -s "$HEAD" "$HEAD".new; then
	mv "$HEAD".new "$HEAD"
	return 1
    fi

    mv "$HEAD".new "$HEAD"
    echo "HEAD up-to-date"
}

get_repo() {
    rm -rf "$TMP_REPO" # just in case
    mkdir -p "$TMP_REPO"
    echo
    git clone --depth 1 "${URL_REMOTE}" "$TMP_REPO" 2>&1
    echo
}

clean_repo() {
    echo "Removing repository from $TMP_REPO"
    rm -rf "$TMP_REPO"
    echo
}

lint_repo() {
    local \
	  FILE_RVAL="${URL}/return-value" \
	  FILE_LINT="${URL}/lint" \
	  FILE_SPDX="${URL}/spdx"
    cd "$TMP_REPO";

    set +e # Danger zone
    echo "Running 'reuse lint'"; reuse lint > "${OLDPWD}/${FILE_LINT}"; echo $? > "${OLDPWD}/${FILE_RVAL}"
    echo "Running 'reuse spdx'"; reuse spdx > "${OLDPWD}/${FILE_SPDX}"
    set -e

    cd "$OLDPWD"; echo
}

# if head was up-to-date, exit successfully
head_was_latest && exit 0

echo "HEAD was outdated, initializing database update"

get_repo
lint_repo
clean_repo
