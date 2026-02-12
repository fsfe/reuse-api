"""Configuration for the REUSE API service."""

from os import getenv


# Flask configuration
TESTING: bool = bool(getenv("FLASK_TESTING", default="0"))
SECRET_KEY: str = getenv("SECRET_KEY", default="secret_key")

# Admin key for the REUSE API, necessary for some operations
ADMIN_KEY: str = getenv("ADMIN_KEY", default="admin_key")

# Configuration for the form server used for registration
FORMS_URL: str = getenv("FORMS_URL", default="https://forms.fsfe.org/email")
FORMS_FILE: str = getenv("FORMS_FILE", default="repos.json")
FORMS_DISABLE: bool = bool(getenv("FORMS_DISABLE", default="0"))

# Number of repository return during pagination
NB_REPOSITORY_BY_PAGINATION: int = int(getenv("NB_REPOSITORY_BY_PAGES", default="10"))

REUSE_DB_PATH: str = getenv("REUSE_DB_PATH", default="/var/lib/reuse/db/")
