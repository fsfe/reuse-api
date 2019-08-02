#!/usr/bin/env python3
#
# SPDX-Copyright: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from setuptools import setup

requirements = ["Flask", "click"]

test_requirements = ["pytest"]


def readme_md():
    """Return contents of README.md"""
    return open("README.md").read()


def changelog_md():
    """Return contents of CHANGELOG.md"""
    return open("CHANGELOG.md").read()


if __name__ == "__main__":
    setup(
        name="reuse-api",
        version="0.1.0",
        url="https://reuse.software/",
        project_urls={
            # "Documentation": "https://reuse.readthedocs.io/",
            "Source": "https://git.fsfe.org/reuse/api"
        },
        license="GPL-3.0-or-later",
        author="Carmen Bianca Bakker",
        author_email="carmenbianca@fsfe.org",
        description="A badge API for REUSE",
        long_description=readme_md() + "\n\n" + changelog_md(),
        long_description_content_type="text/markdown",
        package_dir={"": "src"},
        packages=["reuse_api"],
        include_package_data=True,
        install_requires=requirements,
        tests_require=test_requirements,
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: "
            "GNU General Public License v3 or later (GPLv3+)",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
        ],
    )
