<!--
SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# How to configure reuse-api

Configuration parameters for reuse-api can be set through environment
variables.

For testing and debugging, the default configuration should be suitable for
many use cases. If you need to explicity set any of the parameters, you can
create a `.env` file in the project root directory, which will automatically be
read whenever the "pipenv" virtual environment is entered.

The configuration for the production instance of reuse-api is set in
[`docker-compose.yml`].


## Flask system settings

### `SECRET_KEY`

An arbitary, non-guessable string used by Flask for various security related
purposes. The default value of `"secret_key"` is usable for testing and
debugging, but in a production environment, this parameter should be set
through an evironment variable.


[`docker-compose.yml`]: ../docker-compose.yml
