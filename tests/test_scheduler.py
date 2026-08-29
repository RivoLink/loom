"""Tests for the in-process Scheduler that replaced Scrapyd.

The real-subprocess scenario hits quotes.toscrape.com and is gated by
LOOM_RUN_NETWORK_TESTS=1, matching test_integration_quotes.py.
"""

import os
import time

import pytest

from loom.api.scheduler import Scheduler, UnknownTarget


def test_unknown_target_raises(tmp_path):
    sched = Scheduler(results_dir=str(tmp_path))
    try:
        with pytest.raises(UnknownTarget):
            sched.submit("does_not_exist", {})
    finally:
        sched.shutdown(wait=False)


def test_status_unknown_for_random_id(tmp_path):
    sched = Scheduler(results_dir=str(tmp_path))
    try:
        assert sched.status("not-a-real-job-id") == "unknown"
        assert sched.spider_of("not-a-real-job-id") is None
    finally:
        sched.shutdown(wait=False)


def test_status_finished_when_result_on_disk(tmp_path):
    """If a result file exists for a job_id but the scheduler doesn't know
    about it (e.g. after a restart), status() must return 'finished'."""
    sched = Scheduler(results_dir=str(tmp_path))
    try:
        job_id = "fakerestoredjobid"
        (tmp_path / f"{job_id}.json").write_text("[]")
        assert sched.status(job_id) == "finished"
    finally:
        sched.shutdown(wait=False)


@pytest.mark.skipif(
    os.environ.get("LOOM_RUN_NETWORK_TESTS") != "1",
    reason="set LOOM_RUN_NETWORK_TESTS=1 to enable network-bound tests",
)
def test_submit_real_crawl_lifecycle(tmp_path, monkeypatch):
    from loom import settings as loom_settings

    monkeypatch.setenv("LOOM_RESULTS_DIR", str(tmp_path))
    monkeypatch.setattr(loom_settings, "LOOM_RESULTS_DIR", str(tmp_path))

    sched = Scheduler(results_dir=str(tmp_path))
    try:
        job_id = sched.submit("demo_dom_pagination", {"page": 1})
        assert sched.spider_of(job_id) == "loom"

        deadline = time.time() + 60
        while time.time() < deadline:
            status = sched.status(job_id)
            if status in ("finished", "failed"):
                break
            time.sleep(0.5)

        assert sched.status(job_id) == "finished"
        assert (tmp_path / f"{job_id}.json").exists()
    finally:
        sched.shutdown(wait=True)
