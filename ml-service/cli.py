"""Command-line entry point for the AI candidate matching engine.

Examples:
    python cli.py match --job job.json --candidate candidate.json
    python cli.py rank --job job.json --candidates candidates.json
    python cli.py recommend --candidate candidate.json --jobs jobs.json
"""

from __future__ import annotations

import argparse
import json
import sys

from matcher.core import Candidate, Job, compute_match, rank_candidates, recommend_jobs


def _load(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cmd_match(args):
    job = Job.from_dict(_load(args.job))
    candidate = Candidate.from_dict(_load(args.candidate))
    print(json.dumps(compute_match(job, candidate), indent=2))


def cmd_rank(args):
    job = Job.from_dict(_load(args.job))
    candidates = [Candidate.from_dict(c) for c in _load(args.candidates)]
    print(json.dumps(rank_candidates(job, candidates), indent=2))


def cmd_recommend(args):
    candidate = Candidate.from_dict(_load(args.candidate))
    jobs = [Job.from_dict(j) for j in _load(args.jobs)]
    print(json.dumps(recommend_jobs(candidate, jobs), indent=2))


def main():
    parser = argparse.ArgumentParser(description="AI candidate matching engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_match = subparsers.add_parser("match", help="Score one candidate against one job")
    p_match.add_argument("--job", required=True, help="Path to job JSON file")
    p_match.add_argument("--candidate", required=True, help="Path to candidate JSON file")
    p_match.set_defaults(func=cmd_match)

    p_rank = subparsers.add_parser("rank", help="Rank many candidates for one job")
    p_rank.add_argument("--job", required=True, help="Path to job JSON file")
    p_rank.add_argument("--candidates", required=True, help="Path to a JSON array of candidates")
    p_rank.set_defaults(func=cmd_rank)

    p_recommend = subparsers.add_parser("recommend", help="Rank many jobs for one candidate")
    p_recommend.add_argument("--candidate", required=True, help="Path to candidate JSON file")
    p_recommend.add_argument("--jobs", required=True, help="Path to a JSON array of jobs")
    p_recommend.set_defaults(func=cmd_recommend)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
