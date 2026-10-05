const { computeMatchScore } = require('./aiMatcher');

/**
 * Two-way candidate <-> job matching built on top of the AI screening engine.
 *
 * Application-time screening (applicationController) scores a resume against
 * the one job it was submitted to. This module runs the same engine in bulk:
 *
 *  - recommendJobsForCandidate: rank every open job for a candidate
 *    ("Recommended for you").
 *  - matchCandidatesForJob: rank every candidate on the platform for a job,
 *    including ones who have not applied yet ("Find matching candidates").
 *
 * A candidate's "profile text" is the resume text saved on their profile when
 * available, otherwise a synthetic document built from their headline, bio and
 * declared skills, so candidates without a resume can still be matched.
 */

function buildCandidateProfileText(candidate) {
  if (candidate.resumeText && candidate.resumeText.trim()) return candidate.resumeText;
  return [candidate.title, candidate.bio, (candidate.skills || []).join(' ')]
    .filter(Boolean)
    .join('\n');
}

function hasMatchableProfile(candidate) {
  return Boolean(buildCandidateProfileText(candidate).trim());
}

function summarizeMatch(result) {
  return {
    matchScore: result.score,
    skillMatchPercent: result.skillMatchPercent,
    textSimilarityPercent: result.textSimilarityPercent,
    experienceFitPercent: result.experienceFitPercent,
    matchedSkills: result.matchedSkills,
    missingSkills: result.missingSkills,
  };
}

function byScoreDesc(a, b) {
  return b.match.matchScore - a.match.matchScore;
}

/**
 * @param {object} candidate user document/object (resumeText, skills, title, bio)
 * @param {object[]} jobs job documents/objects
 * @param {object} [options] { limit, minScore }
 * @returns {{ job: object, match: object }[]} sorted best match first
 */
function recommendJobsForCandidate(candidate, jobs, { limit = 10, minScore = 0 } = {}) {
  const profileText = buildCandidateProfileText(candidate);
  return jobs
    .map((job) => ({
      job,
      match: summarizeMatch(computeMatchScore(profileText, job, candidate.skills)),
    }))
    .filter((r) => r.match.matchScore >= minScore)
    .sort(byScoreDesc)
    .slice(0, limit);
}

/**
 * @param {object} job job document/object
 * @param {object[]} candidates user documents/objects
 * @param {object} [options] { limit, minScore }
 * @returns {{ candidate: object, match: object }[]} sorted best match first
 */
function matchCandidatesForJob(job, candidates, { limit = 20, minScore = 0 } = {}) {
  return candidates
    .filter(hasMatchableProfile)
    .map((candidate) => ({
      candidate,
      match: summarizeMatch(
        computeMatchScore(buildCandidateProfileText(candidate), job, candidate.skills)
      ),
    }))
    .filter((r) => r.match.matchScore >= minScore)
    .sort(byScoreDesc)
    .slice(0, limit);
}

module.exports = {
  buildCandidateProfileText,
  recommendJobsForCandidate,
  matchCandidatesForJob,
};
