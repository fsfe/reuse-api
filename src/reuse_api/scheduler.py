# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import re
import subprocess
import time
from queue import Empty, Queue
from threading import Thread
from typing import NamedTuple

from .db import get_db

_LOGGER = logging.getLogger(__name__)
_HASH_PATTERN = re.compile(r"commit (.*):")


class Task(NamedTuple):
    url: str
    hash: str


def hash_from_output(output):
    line = output.strip().split("\n")[0]
    match = _HASH_PATTERN.search(line)
    if match is not None:
        return match.groups()[0]
    return None


def update_task(task, return_code, output):
    if return_code == 0:
        status = 1
    else:
        status = 0
    last_access = time.time()
    new_hash = hash_from_output(output)
    if new_hash is None:
        new_hash = task.hash

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE projects "
        "SET hash=?, status=?, lint_code=?, lint_output=?, last_access=? "
        "WHERE url=?",
        (new_hash, status, return_code, output, last_access, task.url),
    )

    db.commit()


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
            _LOGGER.debug("adding '%s' to queue", task.url)
            _LOGGER.debug("size of queue is %d", self._queue.qsize())
            self._queue.put_nowait(task)
        else:
            _LOGGER.warning(
                "cannot add task to queue when scheduler is not running"
            )

    def run(self):
        self._running = True
        for runner in self._runners:
            runner.start()

    def join(self):
        _LOGGER.debug("finishing the queue")
        self._queue.join()
        _LOGGER.debug("stopping all threads")
        self._running = False
        for runner in self._runners:
            runner.stop()
        for runner in self._runners:
            runner.join()
        _LOGGER.debug("finished stopping all threads")


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

            _LOGGER.debug("linting '%s'", task.url)
            # FIXME!!!!!
            # This step needs to be ABSOLUTELY SECURE!
            try:
                result = subprocess.run(
                    [
                        "ssh",
                        "-i",
                        "~/.ssh/reuse_ed25519",
                        "reuse@wrk1.api.reuse.software",
                        "reuse-lint-repo",
                        task.url,
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    # TODO: Verify whether this timeout is reasonable.
                    timeout=900,
                )
            except subprocess.TimeoutExpired:
                _LOGGER.warning("linting of '%s' timed out", task.url)
            else:
                _LOGGER.debug(
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
