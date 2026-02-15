# How to configure reuse-api

Configuration parameters for reuse-api can be set through environment
variables that can be added to the `Dockerfile`.

The configuration for the production instance of reuse-api is set in
[`docker-compose.yml`].


## Flask system settings

### `SECRET_KEY`

An arbitary, non-guessable string used by Flask for various security related
purposes. The default value of `"secret_key"` is usable for testing and
debugging, but in a production environment, this parameter should be set
through an evironment variable.


[`docker-compose.yml`]: ../docker-compose.yml
