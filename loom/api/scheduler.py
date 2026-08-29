"""In-process scheduler that replaces Scrapyd.

Submits crawls to a multiprocessing Pool with maxtasksperchild=1, so each
crawl runs in a genuinely fresh subprocess. This is required because
Twisted's reactor is a process-level singleton and cannot be restarted
in the same interpreter (second call would raise ReactorNotRestartable).
Fresh subprocess per job also isolates native crashes (lxml, cryptography)
from the API.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from multiprocessing.pool import AsyncResult, Pool
from typing import Literal

from loom.resolver import resolve_spider_name

JobStatus = Literal["pending", "running", "finished", "failed", "unknown"]


class UnknownTarget(Exception):
    """Raised when a `target_name` has neither a YAML config nor a custom spider."""


@dataclass
class JobState:
    job_id: str
    target_name: str
    spider_name: str
    status: JobStatus
    async_result: AsyncResult | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


class Scheduler:
    def __init__(self, results_dir: str, max_workers: int = 1):
        self._jobs: dict[str, JobState] = {}
        # spawn + maxtasksperchild=1 guarantees each crawl gets a fresh
        # Python interpreter, so Twisted's reactor is never reused.
        self._pool = Pool(
            processes=max_workers,
            maxtasksperchild=1,
            context=multiprocessing.get_context("spawn"),
        )
        self._results_dir = results_dir

    def submit(self, target_name: str, params: dict | None) -> str:
        spider_name = resolve_spider_name(target_name)
        if spider_name is None:
            raise UnknownTarget(target_name)
        job_id = uuid.uuid4().hex
        state = JobState(
            job_id=job_id,
            target_name=target_name,
            spider_name=spider_name,
            status="pending",
            started_at=datetime.now(timezone.utc),
        )
        self._jobs[job_id] = state
        state.async_result = self._pool.apply_async(
            _run_crawl_subprocess,
            (spider_name, target_name, params or {}, job_id, self._results_dir),
            callback=lambda _r: self._on_done(job_id, exc=None),
            error_callback=lambda e: self._on_done(job_id, exc=e),
        )
        return job_id

    def _on_done(self, job_id: str, exc: BaseException | None) -> None:
        state = self._jobs[job_id]
        state.finished_at = datetime.now(timezone.utc)
        if exc is not None:
            state.status = "failed"
            state.error = str(exc)
        else:
            state.status = "finished"

    def status(self, job_id: str) -> JobStatus:
        state = self._jobs.get(job_id)
        if state is not None:
            # AsyncResult doesn't expose a queued/running distinction:
            # report "running" for any submitted job until the callback
            # transitions it to "finished" or "failed".
            if state.status == "pending" and state.async_result is not None:
                return "running"
            return state.status
        if os.path.isfile(os.path.join(self._results_dir, f"{job_id}.json")):
            return "finished"
        return "unknown"

    def spider_of(self, job_id: str) -> str | None:
        state = self._jobs.get(job_id)
        return state.spider_name if state else None

    def shutdown(self, wait: bool = True) -> None:
        if wait:
            self._pool.close()
        else:
            self._pool.terminate()
        self._pool.join()


def _run_crawl_subprocess(
    spider_name: str,
    target_name: str,
    params: dict,
    job_id: str,
    results_dir: str,
) -> None:
    """Top-level picklable function executed in a fresh worker process."""
    os.environ.setdefault("LOOM_RESULTS_DIR", results_dir)
    from scrapy.crawler import CrawlerProcess
    from scrapy.settings import Settings

    from loom import settings as loom_settings
    from loom.resolver import resolve_spider_class

    s = Settings()
    s.setmodule(loom_settings, priority="project")
    process = CrawlerProcess(s)
    spider_cls = resolve_spider_class(spider_name)
    process.crawl(
        spider_cls,
        target_name=target_name,
        params=json.dumps(params or {}),
        _job_id=job_id,
    )
    process.start()
