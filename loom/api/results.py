import json
import os

from loom import settings as loom_settings


def result_path(job_id: str) -> str:
    return os.path.join(loom_settings.LOOM_RESULTS_DIR, f"{job_id}.json")


def result_exists(job_id: str) -> bool:
    return os.path.isfile(result_path(job_id))


def read_result(job_id: str) -> list[dict]:
    with open(result_path(job_id), encoding="utf-8") as f:
        return json.load(f)
