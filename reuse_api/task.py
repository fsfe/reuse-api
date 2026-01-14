# SPDX-FileCopyrightText: 2019 Free Software Foundation Europe e.V.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from json import loads as json_loads
from queue import Queue
from threading import Lock
from typing import NamedTuple, override

from reuse_api import models as db

from .models import Repository


class Task(NamedTuple):
    protocol: str
    url: str
    head: str

    def update_db(self, output: str) -> None:
        """Depending on the output, update the information of the repository:
        status, new head hash, status, url, lint code/output, spdx output"""
        # Output is JSON, convert to dict
        output = json_loads(output)

        # Here, we update the URL as well, since it could differ in case from
        # what's stored previously, and we want the info pages to display the URL
        # in the form it was used for the last check.
        Repository.find(self.url).update(
            url=self.url,
            hash=self.head,
            status=(db.Status.OK if output["exit_code"] == 0 else db.Status.BAD),
            lint_code=output["exit_code"],
            lint_output=output["lint_output"],
            spdx_output=output["spdx_output"],
        )


class TaskQueue(Queue):
    # Not SimpleQueue because we want .join()
    """
    Allows to know when a Task is already in the Queue or in computation to
    limit redundant execution
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.task_mutex = Lock()
        self.task_urls = {}

    def __contains__(self, task: Task) -> bool:
        with self.task_mutex:
            return task.url in self.task_urls

    def __len__(self) -> int:
        """Return the number of tasks in the queue"""
        with self.task_mutex:
            return len(self.task_urls)

    @override
    def put_nowait(self, task: Task) -> None:
        with self.task_mutex:
            self.task_urls[task.url] = True
            super().put_nowait(task)

    def done(self, task: Task) -> None:
        with self.task_mutex:
            del self.task_urls[task.url]
        super().task_done()
