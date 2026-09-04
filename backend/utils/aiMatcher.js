const STOPWORDS = require('./stopwords');
const { extractSkills } = require('./skillsDictionary');

/**
 * AI-based resume screening & candidate matching engine.
 *
 * Two independent signals are blended into a single 0-100 match score:
 *
 *  1. Skill overlap: fraction of the job's required skills that are found in
 *     the resume (either via the candidate's declared skills or skills
 *     detected in the resume text against a curated skills dictionary).
 *
 *  2. Semantic text similarity: cosine similarity between the TF (term
 *     frequency) vectors of the resume text and the job description, over
 *     the vocabulary union, after stopword removal and tokenization. This
 *     approximates how closely the resume's language matches the role even
 *     when exact skill keywords are not listed.
 *
 * The blend (65% skills / 35% text) favors concrete, verifiable skill
 * matches while still rewarding resumes whose overall content is topically
 * aligned with the job description.
 */

const SKILL_WEIGHT = 0.65;
const TEXT_WEIGHT = 0.35;

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
 * @param {string} resumeText raw extracted resume text
 * @param {object} job { title, description, skillsRequired }
 * @param {string[]} [candidateDeclaredSkills] skills the candidate listed on their profile
 */
function computeMatchScore(resumeText, job, candidateDeclaredSkills = []) {
  const jobSkills = Array.from(
    new Set((job.skillsRequired || []).map((s) => s.toLowerCase().trim()).filter(Boolean))
  );

  const resumeDetectedSkills = extractSkills(resumeText);
  const candidateSkillSet = new Set(
    [...resumeDetectedSkills, ...(candidateDeclaredSkills || [])].map((s) =>
      s.toLowerCase().trim()
    )
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

  const score = Math.round(
    SKILL_WEIGHT * skillMatchPercent + TEXT_WEIGHT * textSimilarityPercent
  );

  return {
    score: Math.min(100, Math.max(0, score)),
    skillMatchPercent,
    textSimilarityPercent,
    matchedSkills,
    missingSkills,
    extractedSkills: Array.from(candidateSkillSet),
  };
}

module.exports = { computeMatchScore, tokenize, extractSkills };
