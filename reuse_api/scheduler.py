# SPDX-FileCopyrightText: 2023 DB Systel GmbH

import subprocess
from json import JSONDecodeError
from queue import Empty
from threading import Thread
from typing import override

from flask import abort, current_app

from .config import (
    NB_RUNNER,
    REUSE_API,
    SSH_KEY_PATH,
    SSH_KNOW_HOST_PATH,
    SSH_PORT,
    SSH_USER,
)
from .models import Repository
from .task import Task, TaskQueue


class InvalidRepositoryError(Exception):
    pass


def determine_protocol(url: str) -> str:
    """Determine the protocol."""
    # Try these protocols and use the first that works
    try:
        for protocol in ("https", "git", "http"):
            latest_hash(protocol, url)
            return protocol
    except InvalidRepositoryError:
        pass
    raise InvalidRepositoryError


def latest_hash(protocol: str, url: str) -> str:
    """Get the latest hash of the given Git URL using ls-remote"""
    try:
        # pylint: disable=subprocess-run-check
        result = subprocess.run(
            ["git", "ls-remote", f"{protocol}://{url}", "HEAD"],
            stdout=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise InvalidRepositoryError

    if result.returncode != 0:
        raise InvalidRepositoryError

    return result.stdout.decode("utf-8").split()[0]


class Runner(Thread):
    """Defining one task in the schedule queue"""

    def __init__(self, queue, app):
        self._queue = queue
        self._app = app
        self._running: bool = False
        super().__init__()

    @override
    def run(self):
        self._running = True
        while self._running:
            try:
                # The timeout allows the thread to check whether it is still
                # supposed to be running every X seconds.
                task = self._queue.get(timeout=5)
            except Empty:
                continue

            self._app.logger.debug("linting '%s'", task.url)
            try:
                cmd: list[str] = [
                    "ssh",
                    # SSH private key
                    "-i",
                    SSH_KEY_PATH,
                    # accept new host keys, define known_hosts file
                    "-o",
                    "StrictHostKeyChecking=accept-new",
                    "-o",
                    f"UserKnownHostsFile={SSH_KNOW_HOST_PATH}",
                    # SSH host (API worker), and its port
                    f"{SSH_USER}@{REUSE_API}",
                    "-p",
                    str(SSH_PORT),
                    # Command with args (repo URL, verbosity)
                    "reuse_lint_repo",
                    "-r",
                    f"{task.protocol}://{task.url}",
                    "-v",
                ]
                # pylint: disable=subprocess-run-check
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=900,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                self._app.logger.warning("linting of '%s' timed out", task.url)
            else:
                self._app.logger.debug(
                    "finished linting '%s' return code is %d",
                    task.url,
                    result.returncode,
                )
                # If the return code of the SSH connection is 255, we can
                # assume that the SSH connection failed. In this case, we do
                # not update the repository, neither the hash nor the status.
                # Instead, we write a warning that should be monitored.
                error_code: int = 255
                if result.returncode == error_code:
                    self._app.logger.warning(
                        "SSH connection failed when checking '%s'. Not "
                        "updating database. STDERR was: %s",
                        task.url,
                        result.stderr.decode("UTF-8"),
                    )
                else:
                    with self._app.app_context():
                        output: str = result.stdout.decode("utf-8")
                        if not output:  # Check if output is not empty
                            self._app.logger.warning(
                                "No output from linting command for url %s",
                                task.url,
                            )

                        try:  # Update database entry with the results of this check
                            task.update_db(output)

                        except JSONDecodeError as e:
                            self._app.logger.error("Failed to parse JSON output: %s", e)
            finally:
                self._queue.done(task)

    @override
    def join(self, timeout=None) -> None:
        self._running = False
        super().join()


class Scheduler:
    """'Scheduler' is probably a bad name for this class, but I do not know
    what else to call it. It takes tasks and distributes them to runners.
    Except it doesn't even do that, because the runners themselves take the
    tasks from the queue.

    In essence, this is just a container class to hold a queue and some
    runners, and to provide some convenience functions to manage them both.
    """

    def __init__(self, app):
        self._app = app
        self._queue = TaskQueue()
        self._runners = [Runner(self._queue, self._app) for _ in range(NB_RUNNER)]
        self._running: bool = False

    def __contains__(self, task: Task) -> bool:
        return task in self._queue

    def __add_task(self, task: Task) -> None:
        """Add a repository to the check queue"""
        if not self._running:
            current_app.logger.warning(
                "cannot add task to queue when scheduler is not running"
            )
            return False

        if task in self:
            current_app.logger.debug("Task already enqueued: %s", task.url)
            return False

        current_app.logger.info("Task enqueued: %s", task.url)
        self._queue.put_nowait(task)

        current_app.logger.debug("Queue size: %d", len(self._queue))
        return True

    def run(self) -> None:
        """Start scheduler"""
        self._running = True
        for runner in self._runners:
            runner.start()

    def join(self) -> None:
        self._app.logger.debug("finishing the queue")
        self._queue.join()
        self._app.logger.debug("stopping all threads")
        self._running = False
        for runner in self._runners:
            runner.join()
        self._app.logger.debug("finished stopping all threads")

    def schedule(self, url: str, force: bool = False) -> Repository | None:
        """Check whether repo has a new commit and execute check accordingly"""
        current_app.logger.debug("Scheduling %s", url)
        protocol, latest = None, None

        try:
            protocol = determine_protocol(url)
            # TODO: This is an additional request that also happens inside of
            # determine_protocol.
            latest = latest_hash(protocol, url)
        except InvalidRepositoryError:
            abort(400, "Not a Git repository")

        repository = Repository.find(url)
        task_of_repository = Task(protocol, url, latest)

        if repository is None:
            # Create a new entry.
            current_app.logger.debug("No database entry found: %s", url)
            repository = Repository.create(url=url)
            if repository:
                self.__add_task(task_of_repository)
        elif task_of_repository in self:
            current_app.logger.debug("Task enqueued: %s", url)

        elif force:
            current_app.logger.debug("Forcefully scheduling %s", url)
            self.__add_task(task_of_repository)

        elif repository.hash != latest:
            # Make the database entry up-to-date.
            current_app.logger.debug("Repo outdated: %s", url)
            self.__add_task(task_of_repository)
        else:
            current_app.logger.debug("Repo up-to-date: %s", url)

        return repository
