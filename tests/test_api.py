"""Tests for the FastAPI endpoints with a fake Scheduler.

We swap `loom.api.main.scheduler` with an in-process fake so the tests
are fast and deterministic: no real subprocess, no real crawl.
"""

import json

import pytest
from fastapi.testclient import TestClient

from loom.api import main as api_main
from loom.api.scheduler import UnknownTarget


class FakeScheduler:
    """In-memory stand-in for Scheduler.

    submit() returns a deterministic id, immediately writes a stub result
    file, and tracks state. Mimics the public surface (`submit`,
    `status`, `spider_of`).
    """

    def __init__(self, results_dir, known_targets=("demo_dom_pagination",)):
        self.results_dir = results_dir
        self.known_targets = set(known_targets)
        self._counter = 0
        self._jobs: dict[str, dict] = {}

    def submit(self, target_name, params):
        if target_name not in self.known_targets:
            raise UnknownTarget(target_name)
        self._counter += 1
        job_id = f"fakejob{self._counter:04d}"
        spider = "loom" if target_name != "demo_custom_spider" else "demo_custom_spider"
        self._jobs[job_id] = {"status": "finished", "spider": spider}
        # Write a stub result so /result returns 200.
        result_path = f"{self.results_dir}/{job_id}.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump([{"target": target_name, "params": params}], f)
        return job_id

    def status(self, job_id):
        return self._jobs.get(job_id, {}).get("status", "unknown")

    def spider_of(self, job_id):
        return self._jobs.get(job_id, {}).get("spider")


@pytest.fixture
def client(tmp_path, monkeypatch):
    fake = FakeScheduler(results_dir=str(tmp_path))
    monkeypatch.setattr(api_main, "scheduler", fake)
    from loom.api import results as api_results

    monkeypatch.setattr(api_results.loom_settings, "LOOM_RESULTS_DIR", str(tmp_path))
    return TestClient(api_main.app)


def test_post_jobs_returns_202_and_job_id(client):
    r = client.post("/jobs", json={"target_name": "demo_dom_pagination", "params": {"page": 1}})
    assert r.status_code == 202
    body = r.json()
    assert body["job_id"].startswith("fakejob")
    assert body["spider"] == "loom"


def test_post_jobs_unknown_target_returns_404(client):
    r = client.post("/jobs", json={"target_name": "does_not_exist", "params": {}})
    assert r.status_code == 404
    assert "does_not_exist" in r.json()["detail"]


def test_get_status_returns_finished(client):
    r = client.post("/jobs", json={"target_name": "demo_dom_pagination", "params": {}})
    job_id = r.json()["job_id"]
    r = client.get(f"/jobs/{job_id}")
    assert r.status_code == 200
    assert r.json() == {"job_id": job_id, "status": "finished"}


def test_get_status_unknown_job(client):
    r = client.get("/jobs/not-a-real-id")
    assert r.status_code == 200
    assert r.json()["status"] == "unknown"


def test_get_result_returns_items(client):
    r = client.post("/jobs", json={"target_name": "demo_dom_pagination", "params": {"page": 7}})
    job_id = r.json()["job_id"]
    r = client.get(f"/jobs/{job_id}/result")
    assert r.status_code == 200
    body = r.json()
    assert body["job_id"] == job_id
    assert body["items"] == [{"target": "demo_dom_pagination", "params": {"page": 7}}]


def test_get_result_returns_409_when_missing(client):
    r = client.get("/jobs/never-submitted/result")
    assert r.status_code == 409
