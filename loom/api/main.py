from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from loom import settings as loom_settings

from .models import JobAccepted, JobRequest, JobResult, JobStatus
from .results import read_result, result_exists
from .scheduler import Scheduler, UnknownTarget


scheduler = Scheduler(results_dir=loom_settings.LOOM_RESULTS_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Loom API", version="1.0.0", lifespan=lifespan)


@app.post("/jobs", status_code=202, response_model=JobAccepted)
async def submit_job(req: JobRequest) -> JobAccepted:
    try:
        job_id = scheduler.submit(req.target_name, req.params)
    except UnknownTarget:
        raise HTTPException(
            status_code=404,
            detail=f"unknown target_name: {req.target_name!r}",
        )
    return JobAccepted(job_id=job_id, spider=scheduler.spider_of(job_id))


@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_status(job_id: str) -> JobStatus:
    return JobStatus(job_id=job_id, status=scheduler.status(job_id))


@app.get("/jobs/{job_id}/result", response_model=JobResult)
async def get_result(job_id: str) -> JobResult:
    if not result_exists(job_id):
        raise HTTPException(status_code=409, detail="result not available yet")
    return JobResult(job_id=job_id, items=read_result(job_id))
