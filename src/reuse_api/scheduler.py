# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import subprocess
import time
from queue import Empty, Queue
from threading import Thread

_LOGGER = logging.getLogger(__name__)


class Scheduler:
    """'Scheduler' is probably a bad name for this class, but I do not know
    what else to call it. It takes tasks and distributes them to runners.
    Except it doesn't even do that, because the runners themselves take the
    tasks from the queue.

    In essence, this is just a container class to hold a queue and some
    runners, and to provide some convenience functions to manage them both.
    """

    def __init__(self):
        self._queue = Queue()
        self._runners = [Runner(self._queue) for _ in range(6)]
        self._running = False

    def add_task(self, url):
        self._queue.put_nowait(url)
        _LOGGER.debug(f"adding '{url}' to queue'")
        _LOGGER.debug("size of queue is  {}".format(self._queue.qsize()))

    def run(self):
        self._running = True
        for runner in self._runners:
            runner.start()

    def join(self):
        _LOGGER.debug("stopping all threads")
        self._running = False
        for runner in self._runners:
            runner.stop()
        for runner in self._runners:
            runner.join()
        _LOGGER.debug("finished stopping all threads")


class Runner(Thread):
    def __init__(self, queue):
        self._queue = queue
        self._running = False
        super().__init__()

    def run(self):
        self._running = True
        while self._running:
            try:
                # The timeout allows the thread to check whether it is still
                # supposed to be running every X seconds.
                url = self._queue.get(timeout=5)
            except Empty:
                continue

            _LOGGER.debug(f"linting '{url}'")
            # FIXME!!!!!
            # This step needs to be ABSOLUTELY SECURE!
            result = subprocess.run(
                [
                    "ssh",
                    "-i",
                    "~/.ssh/reuse_ed25519",
                    "reuse@wrk1.api.reuse.software",
                    "reuse-lint-repo",
                    url,
                ],
                capture_output=True,
                # TODO: Verify whether this timeout is reasonable.
                timeout=900,
            )
            _LOGGER.debug(
                "finished linting '{url}'. return code is {rcode}".format(
                    url=url, rcode=result.returncode
                )
            )

    def join(self, *args, **kwargs):
        self.stop()
        super().join(*args, **kwargs)

    def stop(self):
        self._running = False
