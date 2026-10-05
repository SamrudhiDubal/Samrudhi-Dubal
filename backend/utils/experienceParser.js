// Lightweight local heuristics for pulling structured signals out of resume
// text: total years of experience mentioned, and the highest education
// level referenced. Both run with simple regex/keyword matching — no
// external NLP service required.

const YEARS_PATTERNS = [
  /(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:professional\s*)?experience/gi,
  /experience\s*(?:of)?\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)/gi,
  /(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s*(?:in|as|working)/gi,
];

/**
 * Best-effort extraction of total years of experience mentioned in resume
 * text. Returns the maximum figure found, or null if nothing matched.
 */
function extractYearsOfExperience(text) {
  if (!text) return null;
  let max = null;
  for (const pattern of YEARS_PATTERNS) {
    for (const match of text.matchAll(pattern)) {
      const years = parseInt(match[1], 10);
      if (!Number.isNaN(years) && years >= 0 && years <= 50) {
        max = max === null ? years : Math.max(max, years);
      }
    }
  }
  return max;
}

// Ordered from highest to lowest so the first match wins.
const EDUCATION_LEVELS = [
  { level: 'phd', keywords: ['ph.d', 'phd', 'doctorate', 'doctoral'] },
  {
    level: 'master',
    keywords: ['master of', 'master\'s', 'msc', 'm.sc', 'mba', 'm.tech', 'mtech', 'ms degree', 'm.s.'],
  },
  {
    level: 'bachelor',
    keywords: [
      'bachelor of',
      "bachelor's",
      'bsc',
      'b.sc',
      'b.tech',
      'btech',
      'b.e.',
      'be degree',
      'bachelor degree',
      'undergraduate degree',
    ],
  },
  { level: 'associate', keywords: ['associate degree', 'associate of'] },
  { level: 'high_school', keywords: ['high school diploma', 'high school'] },
];

/**
 * Detect the highest education level mentioned in resume text.
 * Returns one of 'phd' | 'master' | 'bachelor' | 'associate' | 'high_school' | null.
 */
function extractEducationLevel(text) {
  if (!text) return null;
  const normalized = text.toLowerCase();
  for (const { level, keywords } of EDUCATION_LEVELS) {
    if (keywords.some((kw) => normalized.includes(kw))) {
      return level;
    }
  }
  return null;
}

module.exports = { extractYearsOfExperience, extractEducationLevel };
