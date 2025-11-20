# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
# SPDX-FileCopyrightText: 2023 DB Systel GmbH
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import re
import subprocess
import threading
from queue import Empty, Queue
from threading import Thread
from typing import NamedTuple

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


_HASH_PATTERN = re.compile(r"commit (.*):")


class InvalidRepositoryError(Exception):
    pass


class Task(NamedTuple):
    protocol: str
    url: str
    hash: str

    def update_db(self, output) -> None:
        """Depending on the output, update the information of the repository:
        status, new hash, status, url, lint code/output, spdx output"""
        # Output is JSON, convert to dict
        output = json.loads(output)

        # Here, we update the URL as well, since it could differ in case from
        # what's stored previously, and we want the info pages to display the URL
        # in the form it was used for the last check.
        Repository.find(self.url).update(
            url=self.url,
            hash=self.hash,
            status=("compliant" if output["exit_code"] == 0 else "non-compliant"),
            lint_code=output["exit_code"],
            lint_output=output["lint_output"],
            spdx_output=output["spdx_output"],
        )


class TaskQueue(Queue):
    """
    Allows to know when a Task is already in the Queue or in computation to
    limit redundant execution
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.task_mutex = threading.Lock()
        self.task_urls = {}

    def __contains__(self, task: Task) -> bool:
        with self.task_mutex:
            return task.url in self.task_urls

    def __len__(self) -> int:
        """Return the number of tasks in the queue"""
        with self.task_mutex:
            return len(self.task_urls)

    def put_nowait(self, task: Task, **kwargs) -> None:
        with self.task_mutex:
            self.task_urls[task.url] = True
            super().put_nowait(task, **kwargs)

    def done(self, task: Task) -> None:
        with self.task_mutex:
            del self.task_urls[task.url]
        super().task_done()


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


def schedule_if_new_or_later(url: str, scheduler, force: bool = False):
    """Check whether repo has a new commit and execute check accordingly"""
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
        current_app.logger.debug("no database entry found for '%s'", url)
        repository = Repository.create(url=url)
        if repository:
            scheduler.add_task(task_of_repository)

    elif repository.hash != latest:
        # Make the database entry up-to-date.
        current_app.logger.debug("'%s' is outdated", url)
        scheduler.add_task(task_of_repository)

    elif task_of_repository in scheduler:
        current_app.logger.debug("'%s' already in queue", url)

    elif force:
        current_app.logger.debug("'%s' will be forcefully rechecked", url)
        scheduler.add_task(task_of_repository)

    else:
        current_app.logger.debug("'%s' is still up-to-date", url)

    return repository


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

    def add_task(self, task):
        """Add a repository to the check queue"""
        if self._running:
            self._add_task_if_not_already_enqueue(task)
        else:
            current_app.logger.warning(
                "cannot add task to queue when scheduler is not running"
            )

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
            runner.stop()
        for runner in self._runners:
            runner.join()
        self._app.logger.debug("finished stopping all threads")

    def _add_task_if_not_already_enqueue(self, task) -> bool:
        """Add task to queue if not already in queue.
        Returns true if the task has been added"""
        if task in self:
            current_app.logger.debug("'%s' already in queue", task.url)
            return False

        current_app.logger.debug("adding '%s' to queue", task.url)
        self._queue.put_nowait(task)
        current_app.logger.debug("size of queue is %d", len(self._queue))
        return True


class Runner(Thread):
    """Defining one task in the schedule queue"""

    def __init__(self, queue, app):
        self._queue = queue
        self._app = app
        self._running = False
        super().__init__()

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

                        except json.JSONDecodeError as e:
                            self._app.logger.error("Failed to parse JSON output: %s", e)
            finally:
                self._queue.done(task)

    def join(self, *args, **kwargs) -> None:
        self.stop()
        super().join(*args, **kwargs)

    def stop(self) -> None:
        """Stop the tasks"""
        self._running = False
