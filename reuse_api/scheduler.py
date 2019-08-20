# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import re
import subprocess
from queue import Empty, Queue
from threading import Thread
from typing import NamedTuple

from flask import abort, current_app

from .models import Repository


_HASH_PATTERN = re.compile(r"commit (.*):")


class NotARepository(Exception):
    pass


class Task(NamedTuple):
    protocol: str
    url: str
    hash: str


def schedule_if_new_or_later(url, scheduler):

    # Try these protocols and use the first that works
    for protocol in ("git", "https", "http"):
        try:
            latest = latest_hash(protocol, url)
            break
        except NotARepository:
            pass
    else:
        abort(400, "Not a Git repository")

    repository = Repository.find(url)

    if repository is None:
        # Create a new entry.
        current_app.logger.debug("creating new database entry for '%s'", url)
        repository = Repository.create(url=url, hash=latest)
        scheduler.add_task(Task(protocol, url, latest))

    elif repository.hash != latest:
        # Make the database entry up-to-date.
        current_app.logger.debug("'%s' is outdated", url)
        scheduler.add_task(Task(protocol, url, latest))

    else:
        current_app.logger.debug("'%s' is still up-to-date", url)

    return repository


def latest_hash(protocol, url):
    try:
        result = subprocess.run(
            ["git", "ls-remote", f"{protocol}://{url}", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        raise NotARepository()

    if result.returncode != 0:
        raise NotARepository()
    output = result.stdout.decode("utf-8")
    return output.split()[0]


def hash_from_output(output):
    line = output.strip().split("\n")[0]
    match = _HASH_PATTERN.search(line)
    if match is not None:
        return match.groups()[0]
    return None


def update_task(task, return_code, output):
    if return_code == 0:
        status = "compliant"
    else:
        status = "non-compliant"
    new_hash = hash_from_output(output)
    if new_hash is None:
        new_hash = task.hash

    Repository.find(task.url).update(
        hash=new_hash, status=status, lint_code=return_code, lint_output=output
    )


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
        self._queue = Queue()
        self._runners = [Runner(self._queue, self._app) for _ in range(6)]
        self._running = False

    def add_task(self, task):
        if self._running:
            current_app.logger.debug("adding '%s' to queue", task.url)
            current_app.logger.debug(
                "size of queue is %d", self._queue.qsize()
            )
            self._queue.put_nowait(task)
        else:
            current_app.logger.warning(
                "cannot add task to queue when scheduler is not running"
            )

    def run(self):
        self._running = True
        for runner in self._runners:
            runner.start()

    def join(self):
        self._app.logger.debug("finishing the queue")
        self._queue.join()
        self._app.logger.debug("stopping all threads")
        self._running = False
        for runner in self._runners:
            runner.stop()
        for runner in self._runners:
            runner.join()
        self._app.logger.debug("finished stopping all threads")


class Runner(Thread):
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
            # FIXME!!!!!
            # This step needs to be ABSOLUTELY SECURE!
            try:
                result = subprocess.run(
                    [
                        "ssh",
                        "-i",
                        "~/.ssh/reuse_ed25519",
                        "-o",
                        "StrictHostKeyChecking=accept-new",
                        "-o",
                        "UserKnownHostsFile=~/.ssh/known_hosts",
                        "reuse@wrk1.api.reuse.software",
                        "reuse-lint-repo",
                        f"{task.protocol}://{task.url}",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    # TODO: Verify whether this timeout is reasonable.
                    timeout=900,
                )
            except subprocess.TimeoutExpired:
                self._app.logger.warning("linting of '%s' timed out", task.url)
            else:
                self._app.logger.debug(
                    "finished linting '%s' return code is %d",
                    task.url,
                    result.returncode,
                )
                with self._app.app_context():
                    update_task(
                        task, result.returncode, result.stdout.decode("utf-8")
                    )
            finally:
                self._queue.task_done()

    def join(self, *args, **kwargs):
        self.stop()
        super().join(*args, **kwargs)

    def stop(self):
        self._running = False
