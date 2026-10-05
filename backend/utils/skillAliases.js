// Canonical skill -> list of common aliases/synonyms. Used so that, e.g., a
// job requiring "javascript" matches a resume that only says "js", and a
// resume written as "node" is recognized as the same skill as "node.js".
const SKILL_ALIASES = {
  javascript: ['js', 'es6', 'ecmascript'],
  typescript: ['ts'],
  'node.js': ['node', 'nodejs'],
  'react.js': ['react', 'reactjs'],
  'vue.js': ['vue', 'vuejs'],
  'next.js': ['nextjs', 'next'],
  'express.js': ['express', 'expressjs'],
  mongodb: ['mongo'],
  postgresql: ['postgres', 'psql'],
  kubernetes: ['k8s'],
  'machine learning': ['ml'],
  'deep learning': ['dl'],
  'natural language processing': ['nlp'],
  'artificial intelligence': ['ai'],
  'continuous integration': ['ci/cd', 'ci', 'cd'],
  'ui/ux': ['ux', 'ui', 'ux/ui'],
  'google cloud': ['gcp'],
  'amazon web services': ['aws'],
  golang: ['go'],
  'c#': ['csharp', 'c-sharp'],
  'c++': ['cpp'],
  'ruby on rails': ['rails'],
  rest: ['restful', 'rest api', 'restful api'],
  sql: ['structured query language'],
};

// Reverse lookup: alias -> canonical skill name.
const ALIAS_TO_CANONICAL = Object.entries(SKILL_ALIASES).reduce((acc, [canonical, aliases]) => {
  for (const alias of aliases) {
    acc[alias.toLowerCase()] = canonical;
  }
  return acc;
}, {});

/**
 * Resolve a skill string (as typed by an employer or detected in a resume)
 * to its canonical form, so equivalent spellings compare equal.
 */
function toCanonicalSkill(skill) {
  const normalized = skill.toLowerCase().trim();
  return ALIAS_TO_CANONICAL[normalized] || normalized;
}

module.exports = { SKILL_ALIASES, ALIAS_TO_CANONICAL, toCanonicalSkill };
