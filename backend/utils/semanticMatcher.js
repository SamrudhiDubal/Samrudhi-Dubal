// Optional LLM-based semantic resume screening layer.
//
// When ANTHROPIC_API_KEY is configured, each application gets a qualitative
// semantic match score + short rationale from Claude, blended with the local
// skill/text/experience score computed by aiMatcher.js. When no API key is
// set, this module is a no-op and the engine runs entirely on the local
// scoring in aiMatcher.js — no external calls, no required configuration.
let Anthropic;
try {
  // Lazily required so the backend still runs without this optional dependency installed.
  Anthropic = require('@anthropic-ai/sdk');
} catch {
  Anthropic = null;
}

let client = null;
function getClient() {
  if (!Anthropic || !process.env.ANTHROPIC_API_KEY) return null;
  if (!client) client = new Anthropic();
  return client;
}

const MAX_CHARS = 6000;
const truncate = (text) => (text || '').slice(0, MAX_CHARS);

/**
 * Ask Claude to rate how well a resume fits a job, as a secondary signal on
 * top of the local skill/text-similarity scoring. Returns
 * { score: 0-100, summary: string } or null if unavailable/unconfigured/failed.
 * Never throws — a failure here must not block an application submission.
 */
async function getSemanticMatch(resumeText, job) {
  const anthropic = getClient();
  if (!anthropic || !resumeText) return null;

  try {
    const response = await anthropic.messages.create({
      model: 'claude-opus-5-5',
      max_tokens: 400,
      output_config: { effort: 'low' },
      system:
        'You are an expert technical recruiter screening a resume against a job posting. ' +
        'Respond with ONLY a JSON object of the exact shape {"score": <integer 0-100>, "summary": <string, max 40 words>} ' +
        'and no other text. "score" is how well the candidate fits the role overall (skills, seniority, domain relevance). ' +
        '"summary" briefly explains the score in plain language for a hiring manager.',
      messages: [
        {
          role: 'user',
          content:
            `Job title: ${job.title || 'N/A'}\n` +
            `Job description: ${truncate(job.description)}\n` +
            `Required skills: ${(job.skillsRequired || []).join(', ') || 'N/A'}\n\n` +
            `Resume:\n${truncate(resumeText)}`,
        },
      ],
    });

    const textBlock = response.content.find((block) => block.type === 'text');
    if (!textBlock) return null;

    const match = textBlock.text.match(/\{[\s\S]*\}/);
    if (!match) return null;

    const parsed = JSON.parse(match[0]);
    const score = Math.min(100, Math.max(0, Math.round(Number(parsed.score))));
    if (Number.isNaN(score)) return null;

    return { score, summary: String(parsed.summary || '').slice(0, 300) };
  } catch (err) {
    console.error('Semantic match unavailable, continuing with local score only:', err.message);
    return null;
  }
}

module.exports = { getSemanticMatch };
