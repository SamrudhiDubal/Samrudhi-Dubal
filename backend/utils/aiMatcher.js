const STOPWORDS = require('./stopwords');
const { extractSkills } = require('./skillsDictionary');
const { toCanonicalSkill } = require('./skillAliases');
const { extractYearsOfExperience, extractEducationLevel } = require('./experienceParser');

/**
 * AI-based resume screening & candidate matching engine.
 *
 * Three independent signals are blended into a single 0-100 match score:
 *
 *  1. Skill overlap (50%): fraction of the job's required skills that are
 *     found in the resume (via declared profile skills or skills detected
 *     against a curated dictionary + alias/synonym table, e.g. "js" is
 *     recognized as "javascript").
 *
 *  2. Semantic text similarity (25%): cosine similarity between the TF
 *     (term frequency) vectors of the resume text and the job description,
 *     over the vocabulary union, after tokenization and stopword removal.
 *     This rewards resumes whose overall content is topically aligned with
 *     the job even when exact skill keywords are not listed.
 *
 *  3. Experience fit (25%): years of experience mentioned in the resume,
 *     compared against the minimum years typically expected for the job's
 *     experience level (entry/mid/senior/lead). Unknown (not mentioned) is
 *     scored neutrally rather than penalized.
 *
 * Education level is also detected and surfaced for employers, but is
 * informational only (not weighted into the score), since many strong
 * candidates have non-traditional backgrounds.
 *
 * Everything here runs locally with no external AI API calls required.
 */

const SKILL_WEIGHT = 0.5;
const TEXT_WEIGHT = 0.25;
const EXPERIENCE_WEIGHT = 0.25;

// Minimum years of experience typically expected per level, used only to
// gauge experience fit — not a hard requirement.
const EXPERIENCE_LEVEL_MIN_YEARS = {
  entry: 0,
  mid: 2,
  senior: 5,
  lead: 8,
};

function tokenize(text) {
  if (!text) return [];
  return text
    .toLowerCase()
    .replace(/[^a-z0-9+.#\s]/g, ' ')
    .split(/\s+/)
    .filter((tok) => tok.length > 1 && !STOPWORDS.has(tok));
}

function termFrequency(tokens) {
  const freq = new Map();
  for (const tok of tokens) {
    freq.set(tok, (freq.get(tok) || 0) + 1);
  }
  return freq;
}

function cosineSimilarity(freqA, freqB) {
  const vocab = new Set([...freqA.keys(), ...freqB.keys()]);
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (const term of vocab) {
    const a = freqA.get(term) || 0;
    const b = freqB.get(term) || 0;
    dot += a * b;
    normA += a * a;
    normB += b * b;
  }
  if (normA === 0 || normB === 0) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

/**
 * How well a candidate's detected years of experience fits a job's
 * experience level. Returns a 0-100 score, or null if the resume didn't
 * mention a number of years (treated neutrally by the caller).
 */
function computeExperienceFit(candidateYears, jobExperienceLevel) {
  if (candidateYears === null || candidateYears === undefined) return null;
  const requiredMin = EXPERIENCE_LEVEL_MIN_YEARS[jobExperienceLevel] ?? 0;
  if (requiredMin === 0) return 100;
  if (candidateYears >= requiredMin) return 100;
  return Math.round((candidateYears / requiredMin) * 100);
}

/**
 * @param {string} resumeText raw extracted resume text
 * @param {object} job { title, description, skillsRequired, experienceLevel }
 * @param {string[]} [candidateDeclaredSkills] skills the candidate listed on their profile
 */
function computeMatchScore(resumeText, job, candidateDeclaredSkills = []) {
  const jobSkills = Array.from(
    new Set((job.skillsRequired || []).map((s) => toCanonicalSkill(s)).filter(Boolean))
  );

  const resumeDetectedSkills = extractSkills(resumeText);
  const candidateSkillSet = new Set(
    [...resumeDetectedSkills, ...(candidateDeclaredSkills || [])].map((s) => toCanonicalSkill(s))
  );

  const matchedSkills = jobSkills.filter((skill) => candidateSkillSet.has(skill));
  const missingSkills = jobSkills.filter((skill) => !candidateSkillSet.has(skill));
  const skillMatchPercent =
    jobSkills.length === 0 ? 100 : Math.round((matchedSkills.length / jobSkills.length) * 100);

  const jobText = `${job.title || ''} ${job.description || ''} ${jobSkills.join(' ')}`;
  const resumeFreq = termFrequency(tokenize(resumeText));
  const jobFreq = termFrequency(tokenize(jobText));
  const similarity = cosineSimilarity(resumeFreq, jobFreq);
  const textSimilarityPercent = Math.round(similarity * 100);

  const candidateYears = extractYearsOfExperience(resumeText);
  const educationLevel = extractEducationLevel(resumeText);
  const experienceFitPercent = computeExperienceFit(candidateYears, job.experienceLevel);

  // Redistribute the experience weight onto skills/text when experience
  // couldn't be determined, so the score stays on a comparable 0-100 scale.
  let score;
  if (experienceFitPercent === null) {
    const redistributed = SKILL_WEIGHT + EXPERIENCE_WEIGHT * (SKILL_WEIGHT / (SKILL_WEIGHT + TEXT_WEIGHT));
    const redistributedText = TEXT_WEIGHT + EXPERIENCE_WEIGHT * (TEXT_WEIGHT / (SKILL_WEIGHT + TEXT_WEIGHT));
    score = Math.round(redistributed * skillMatchPercent + redistributedText * textSimilarityPercent);
  } else {
    score = Math.round(
      SKILL_WEIGHT * skillMatchPercent +
        TEXT_WEIGHT * textSimilarityPercent +
        EXPERIENCE_WEIGHT * experienceFitPercent
    );
  }

  return {
    score: Math.min(100, Math.max(0, score)),
    skillMatchPercent,
    textSimilarityPercent,
    experienceFitPercent,
    candidateYearsOfExperience: candidateYears,
    educationLevel,
    matchedSkills,
    missingSkills,
    extractedSkills: Array.from(candidateSkillSet),
  };
}

module.exports = { computeMatchScore, tokenize, extractSkills, computeExperienceFit };
