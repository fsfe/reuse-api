# SPDX-FileCopyrightText: 2026 Free Software Foundation Europe <https://fsfe.org>
#
# SPDX-License-Identifier: CC0-1.0

# This should *not* be the default development environment as Nix has different
# package versions that Alpine (maybe even different features).  This is merely
# a convinience wrapper for Nix users wanting to try out the project locally.

{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  nativeBuildInputs = with pkgs; [
    (python312.withPackages (py: [ # keep this in sync with alpine versions
      py.flask-wtf py.email-validator
      py.requests
      py.gunicorn

      # dev packages
      py.pytest
      py.pytest-cov
      py.pytest-mypy
      py.requests-mock
      # py.types-requests # alpine is missing it so it should not be used
    ]))
    git
    ruff
  ];
  shellHook =''
    PATH="$PATH:$PWD/bin"
    export FLASK_DEBUG=1
    export FLASK_TESTING=1
    export REUSE_DB_PATH="/tmp/reuse-api-db/"

    alias run="flask --app reuse_api run"
    alias t="pytest"
  '';
}
