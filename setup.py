#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from setuptools import find_namespace_packages, setup


setup(
    name="reuse-api",
    description="A badge API for REUSE",
    url="https://git.fsfe.org/reuse/api",
    author="Carmen Bianca Bakker",
    author_email="carmenbianca@fsfe.org",
    license="GPL-3.0-or-later",
    packages=find_namespace_packages(),
    include_package_data=True,
    zip_safe=False,
)
