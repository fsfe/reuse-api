# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Configuration for the REUSE API service"""


# Configuration for the repository storage
SQLALCHEMY_DATABASE_URI = f"sqlite:///{instance_path}/database.sqlite"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# TODO: SERVERNAME
