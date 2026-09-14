"""FastAPI microservice exposing the AI candidate-matching engine.

Run locally with:

    uvicorn app:app --reload --port 8000

Endpoints:
    GET  /health                 liveness check
    POST /api/match              score one candidate against one job
    POST /api/rank-candidates    rank many candidates for one job (employer view)
    POST /api/recommend-jobs     rank many jobs for one candidate (candidate view)
    POST /api/parse-resume       upload a resume file, get extracted text + detected skills
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from matcher.core import Candidate, Job, compute_match, rank_candidates, recommend_jobs
from matcher.resume_parser import ResumeParseError, extract_resume_text
from matcher.skills import extract_skills

app = FastAPI(
    title="AI Candidate Matching Service",
    description="Intelligent, explainable candidate <-> job matching engine.",
    version="1.0.0",
)


class JobIn(BaseModel):
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_level: str = "entry"
    location: Optional[str] = None


class CandidateIn(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    resume_text: str = ""
    declared_skills: list[str] = Field(default_factory=list)
    experience_years: Optional[float] = None
    location: Optional[str] = None


class MatchRequest(BaseModel):
    job: JobIn
    candidate: CandidateIn


class RankCandidatesRequest(BaseModel):
    job: JobIn
    candidates: list[CandidateIn]


class RecommendJobsRequest(BaseModel):
    candidate: CandidateIn
    jobs: list[JobIn]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/match")
def match(payload: MatchRequest):
    job = Job.from_dict(payload.job.model_dump())
    candidate = Candidate.from_dict(payload.candidate.model_dump())
    return compute_match(job, candidate)


@app.post("/api/rank-candidates")
def rank_candidates_endpoint(payload: RankCandidatesRequest):
    job = Job.from_dict(payload.job.model_dump())
    candidates = [Candidate.from_dict(c.model_dump()) for c in payload.candidates]
    return {"job_id": job.id, "results": rank_candidates(job, candidates)}


@app.post("/api/recommend-jobs")
def recommend_jobs_endpoint(payload: RecommendJobsRequest):
    candidate = Candidate.from_dict(payload.candidate.model_dump())
    jobs = [Job.from_dict(j.model_dump()) for j in payload.jobs]
    return {"candidate_id": candidate.id, "results": recommend_jobs(candidate, jobs)}


@app.post("/api/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    file_bytes = await file.read()
    try:
        text = extract_resume_text(file_bytes, file.filename)
    except ResumeParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"text": text, "detected_skills": extract_skills(text)}
